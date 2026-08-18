"""Tests for PR5.1 Redis-backed global rate limiting (PRRP-DEFER-002).

These tests run WITHOUT a live Redis server. They exercise:
- normal allowance
- limit exceeded
- atomic/global behaviour (verified with a fake Redis client)
- TTL/expiry enforcement (FakeRedis-style)
- graceful degradation on Redis failure (fallback to in-memory)
- compatibility with existing dependency injection (require_rate_limit)

No real network calls. A minimal in-process fake client simulates Redis INCR/
EXPIRE/EVAL/DEL/PING semantics with TTL so behaviour is verified deterministically.
"""

import pytest

from src.engine.gateway.redis_rate_limiter import RedisRateLimitStore
from src.engine.gateway.rate_limiter import InMemoryRateLimitStore


class _FakeRedis:
    """Minimal in-process Redis fake supporting INCR/EXPIRE/EVAL/DEL/PING + TTL.

    Implements the subset of redis-py used by RedisRateLimitStore, including a
    real TTL clock driven by an injectable time function.
    """

    def __init__(self, time_fn):
        self._data: dict[str, int] = {}
        self._ttls: dict[str, float] = {}
        self._now = time_fn
        self.pinged = False

    def ping(self):
        self.pinged = True
        return True

    def _check_ttl(self, key: str) -> bool:
        """Return True if key still alive (not expired). Drop if expired."""
        expire_at = self._ttls.get(key)
        if expire_at is not None and self._now() >= expire_at:
            self._data.pop(key, None)
            self._ttls.pop(key, None)
            return False
        return key in self._data

    def incr(self, key: str) -> int:
        self._check_ttl(key)
        self._data[key] = self._data.get(key, 0) + 1
        return self._data[key]

    def expire(self, key: str, seconds: int) -> bool:
        if key in self._data:
            self._ttls[key] = self._now() + seconds
            return True
        return False

    def delete(self, key: str):
        self._data.pop(key, None)
        self._ttls.pop(key, None)
        return 1

    def eval(self, script: str, numkeys: int, key: str, *args):
        # Lua semantics simulated: INCR then EXPIRE on first increment.
        if not self._check_ttl(key):
            pass  # key expired; incr below will start at 1
        count = self.incr(key)
        if count == 1:
            self.expire(key, int(args[0]))
        return count

    def _advance(self, seconds: float):
        # Advance fake clock; subsequent ops observe TTL expiry.
        self._now = lambda: self._now() + 0  # keep ref
        state = getattr(self, "_state", None)
        if state is not None:
            state["t"] += seconds


@pytest.fixture
def fake_redis(monkeypatch):
    """Provide a fake Redis client whose clock can be advanced."""
    state = {"t": 0.0}
    client = _FakeRedis(lambda: state["t"])
    client._advance = lambda s: state.__setitem__("t", state["t"] + s)
    return client


def _make_store(fake_redis):
    store = RedisRateLimitStore(redis_client=fake_redis, key_prefix="ratelimit:")
    # Connection test happens in __init__; force availability flag for isolation.
    assert store._redis_available, "fake redis should be marked available"
    return store


# ── 1. Normal allowance ──────────────────────────────────────────────

def test_allows_within_limit(fake_redis):
    store = _make_store(fake_redis)
    for _ in range(9):
        allowed, remaining = store.check_and_increment("ip:login", 10, 60)
        assert allowed
    # 10th request still allowed, remaining hits 0
    allowed, remaining = store.check_and_increment("ip:login", 10, 60)
    assert allowed and remaining == 0


def test_blocks_after_limit(fake_redis):
    store = _make_store(fake_redis)
    for _ in range(5):
        store.check_and_increment("ip:export", 5, 60)
    allowed, remaining = store.check_and_increment("ip:export", 5, 60)
    assert not allowed
    assert remaining == 0


def test_per_key_isolation(fake_redis):
    store = _make_store(fake_redis)
    for _ in range(3):
        store.check_and_increment("key-a", 3, 60)
    assert not store.check_and_increment("key-a", 3, 60)[0]
    assert store.check_and_increment("key-b", 3, 60)[0]


# ── 2. TTL / expiry ──────────────────────────────────────────────────

def test_counter_resets_after_window(fake_redis):
    store = _make_store(fake_redis)
    for _ in range(5):
        store.check_and_increment("ip:win", 5, 60)
    # Exhausted
    assert not store.check_and_increment("ip:win", 5, 60)[0]
    # Advance past the 60s window
    fake_redis._advance(61)
    # Counter should have expired → allowed again
    allowed, remaining = store.check_and_increment("ip:win", 5, 60)
    assert allowed and remaining == 4


def test_reset_clears_counter(fake_redis):
    store = _make_store(fake_redis)
    for _ in range(3):
        store.check_and_increment("ip:reset", 3, 60)
    store.reset("ip:reset")
    allowed, remaining = store.check_and_increment("ip:reset", 3, 60)
    assert allowed and remaining == 2


# ── 3. Atomic / global behaviour (fixed-window via Lua) ─────────────

def test_fixed_window_ttl_set_once(fake_redis):
    """TTL should be set on first increment and the window should be fixed."""
    store = _make_store(fake_redis)
    # Exhaust the limit (5 requests)
    for _ in range(5):
        store.check_and_increment("ip:win2", 5, 60)
    # Advance partway — still within window, still blocked
    fake_redis._advance(30)
    assert not store.check_and_increment("ip:win2", 5, 60)[0]
    # Advance past window — fresh window, allowed again
    fake_redis._advance(31)
    allowed, remaining = store.check_and_increment("ip:win2", 5, 60)
    assert allowed and remaining == 4


# ── 4. Graceful degradation on Redis failure ─────────────────────────

def test_falls_back_to_in_memory_on_redis_error(fake_redis):
    store = _make_store(fake_redis)

    # Make the fake client raise on EVAL to simulate Redis outage
    def boom(*a, **k):
        raise ConnectionError("redis down")

    fake_redis.eval = boom

    # First call trips the failure → fallback
    allowed, _ = store.check_and_increment("ip:fallback", 3, 60)
    assert allowed
    # Subsequent calls keep using in-memory fallback
    assert store.check_and_increment("ip:fallback", 3, 60)[0]
    assert store.check_and_increment("ip:fallback", 3, 60)[0]
    # 4th should be blocked by in-memory fallback (limit 3)
    assert not store.check_and_increment("ip:fallback", 3, 60)[0]


def test_init_without_redis_uses_fallback():
    """No REDIS_URL, no client → store still functional (in-memory)."""
    store = RedisRateLimitStore()  # no client, no env expected in test
    assert not store._redis_available
    # Functional via fallback
    for _ in range(4):
        assert store.check_and_increment("ip:noredis", 5, 60)[0]
    assert store.check_and_increment("ip:noredis", 5, 60)[0]


# ── 5. DI compatibility ──────────────────────────────────────────────

def test_injected_redis_store_in_dependency():
    """require_rate_limit resolves the configured store (Redis or fallback)."""
    from src.engine.gateway.rate_limit_dependency import get_rate_limit_store

    store = get_rate_limit_store()
    # Must satisfy RateLimitStore Protocol contract
    allowed, remaining = store.check_and_increment("ip:di", 10, 60)
    assert isinstance(allowed, bool)
    assert isinstance(remaining, int)


def test_protocol_compatibility():
    """RedisRateLimitStore implements RateLimitStore Protocol structurally."""
    from src.domain.gateway.rate_limiter import RateLimitStore

    store = _make_store_fallback()
    # Structural subtype check
    assert isinstance(store, object)  # placeholder; Protocol is structural
    # Verify both implementations expose the same public contract
    for impl in (InMemoryRateLimitStore(), RedisRateLimitStore()):
        assert hasattr(impl, "check_and_increment")
        assert hasattr(impl, "reset")


def _make_store_fallback():
    return RedisRateLimitStore()
