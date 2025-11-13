"""
Cache Manager - Redis caching for captions, hashtags, and performance data.
Provides high-performance caching with TTL and cache invalidation.
"""

import asyncio
import json
import logging
import pickle
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    ttl: Optional[int]  # seconds
    created_at: datetime
    hits: int = 0
    last_accessed: Optional[datetime] = None

class CacheManager:
    """Redis-based cache manager for high-performance data caching."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis: Optional[redis.Redis] = None
        self._local_cache: Dict[str, CacheEntry] = {}  # For metrics and fast access
        self._running = False

        # Cache namespaces
        self.namespaces = {
            'captions': 'caption:',
            'hashtags': 'hashtag:',
            'videos': 'video:',
            'analytics': 'analytics:',
            'users': 'user:',
            'system': 'system:'
        }

        # Metrics
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'hit_rate': 0.0
        }

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(self.redis_url)
            await self.redis.ping()  # Test connection
            logger.info("CacheManager connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
        logger.info("CacheManager disconnected from Redis")

    async def start(self):
        """Start the cache manager."""
        if not self.redis:
            await self.connect()

        self._running = True

        # Start background cleanup task
        asyncio.create_task(self._cleanup_expired_entries())

        logger.info("CacheManager started")

    async def stop(self):
        """Stop the cache manager."""
        self._running = False
        await self.disconnect()

    # Core cache operations

    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                  namespace: str = None) -> bool:
        """Set a cache entry."""
        if not self.redis:
            await self.connect()

        full_key = self._get_full_key(key, namespace)
        actual_ttl = ttl or self.default_ttl

        try:
            # Serialize value
            serialized_value = self._serialize(value)

            # Store in Redis with TTL
            await self.redis.setex(full_key, actual_ttl, serialized_value)

            # Update local cache for metrics
            self._local_cache[full_key] = CacheEntry(
                key=full_key,
                value=value,
                ttl=actual_ttl,
                created_at=datetime.utcnow()
            )

            self.metrics['sets'] += 1
            logger.debug(f"Cached key: {full_key} (TTL: {actual_ttl}s)")

            return True

        except Exception as e:
            logger.error(f"Failed to cache key {full_key}: {e}")
            return False

    async def get(self, key: str, namespace: str = None) -> Any:
        """Get a cache entry."""
        if not self.redis:
            await self.connect()

        full_key = self._get_full_key(key, namespace)

        try:
            # Get from Redis
            serialized_value = await self.redis.get(full_key)

            if serialized_value is None:
                self.metrics['misses'] += 1
                return None

            # Deserialize value
            value = self._deserialize(serialized_value)

            # Update local cache metrics
            if full_key in self._local_cache:
                entry = self._local_cache[full_key]
                entry.hits += 1
                entry.last_accessed = datetime.utcnow()

            self.metrics['hits'] += 1
            self._update_hit_rate()

            logger.debug(f"Cache hit for key: {full_key}")
            return value

        except Exception as e:
            logger.error(f"Failed to get cached key {full_key}: {e}")
            self.metrics['misses'] += 1
            return None

    async def delete(self, key: str, namespace: str = None) -> bool:
        """Delete a cache entry."""
        if not self.redis:
            await self.connect()

        full_key = self._get_full_key(key, namespace)

        try:
            result = await self.redis.delete(full_key)

            if result > 0:
                # Remove from local cache
                if full_key in self._local_cache:
                    del self._local_cache[full_key]

                self.metrics['deletes'] += 1
                logger.debug(f"Deleted cached key: {full_key}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to delete cached key {full_key}: {e}")
            return False

    async def exists(self, key: str, namespace: str = None) -> bool:
        """Check if a cache entry exists."""
        if not self.redis:
            await self.connect()

        full_key = self._get_full_key(key, namespace)

        try:
            return await self.redis.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Failed to check existence of key {full_key}: {e}")
            return False

    async def expire(self, key: str, ttl: int, namespace: str = None) -> bool:
        """Set expiration time for a cache entry."""
        if not self.redis:
            await self.connect()

        full_key = self._get_full_key(key, namespace)

        try:
            result = await self.redis.expire(full_key, ttl)

            if result and full_key in self._local_cache:
                self._local_cache[full_key].ttl = ttl

            return result
        except Exception as e:
            logger.error(f"Failed to set expiration for key {full_key}: {e}")
            return False

    async def ttl(self, key: str, namespace: str = None) -> int:
        """Get TTL for a cache entry."""
        if not self.redis:
            await self.connect()

        full_key = self._get_full_key(key, namespace)

        try:
            return await self.redis.ttl(full_key)
        except Exception as e:
            logger.error(f"Failed to get TTL for key {full_key}: {e}")
            return -1

    # Batch operations

    async def mset(self, key_value_pairs: Dict[str, Any],
                   ttl: Optional[int] = None, namespace: str = None) -> bool:
        """Set multiple cache entries."""
        if not self.redis:
            await self.connect()

        try:
            pipeline = self.redis.pipeline()

            for key, value in key_value_pairs.items():
                full_key = self._get_full_key(key, namespace)
                serialized_value = self._serialize(value)
                actual_ttl = ttl or self.default_ttl

                pipeline.setex(full_key, actual_ttl, serialized_value)

                # Update local cache
                self._local_cache[full_key] = CacheEntry(
                    key=full_key,
                    value=value,
                    ttl=actual_ttl,
                    created_at=datetime.utcnow()
                )

            await pipeline.execute()

            self.metrics['sets'] += len(key_value_pairs)
            return True

        except Exception as e:
            logger.error(f"Failed to batch set cache entries: {e}")
            return False

    async def mget(self, keys: List[str], namespace: str = None) -> Dict[str, Any]:
        """Get multiple cache entries."""
        if not self.redis:
            await self.connect()

        try:
            full_keys = [self._get_full_key(key, namespace) for key in keys]
            serialized_values = await self.redis.mget(full_keys)

            results = {}
            for key, full_key, serialized_value in zip(keys, full_keys, serialized_values):
                if serialized_value is not None:
                    value = self._deserialize(serialized_value)
                    results[key] = value

                    # Update metrics
                    if full_key in self._local_cache:
                        entry = self._local_cache[full_key]
                        entry.hits += 1
                        entry.last_accessed = datetime.utcnow()

                    self.metrics['hits'] += 1
                else:
                    self.metrics['misses'] += 1

            self._update_hit_rate()
            return results

        except Exception as e:
            logger.error(f"Failed to batch get cache entries: {e}")
            return {}

    # Namespace-specific operations

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all entries in a namespace."""
        if not self.redis:
            await self.connect()

        try:
            pattern = f"{self.namespaces.get(namespace, namespace)}*"
            keys = await self.redis.keys(pattern)

            if keys:
                await self.redis.delete(*keys)

                # Remove from local cache
                for key in keys:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    if key_str in self._local_cache:
                        del self._local_cache[key_str]

                self.metrics['deletes'] += len(keys)
                logger.info(f"Cleared {len(keys)} entries from namespace: {namespace}")
                return len(keys)
            else:
                return 0

        except Exception as e:
            logger.error(f"Failed to clear namespace {namespace}: {e}")
            return 0

    # Specialized caching methods for AI pipeline

    async def cache_caption(self, task_id: str, caption: str, hashtags: List[str],
                          ttl: int = 1800) -> bool:
        """Cache generated caption and hashtags."""
        data = {
            'caption': caption,
            'hashtags': hashtags,
            'generated_at': datetime.utcnow().isoformat()
        }
        return await self.set(f"caption:{task_id}", data, ttl, 'captions')

    async def get_cached_caption(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get cached caption and hashtags."""
        return await self.get(f"caption:{task_id}", 'captions')

    async def cache_video_metadata(self, video_id: str, metadata: Dict[str, Any],
                                 ttl: int = 3600) -> bool:
        """Cache video metadata."""
        return await self.set(f"metadata:{video_id}", metadata, ttl, 'videos')

    async def get_cached_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get cached video metadata."""
        return await self.get(f"metadata:{video_id}", 'videos')

    async def cache_analytics(self, post_id: str, analytics: Dict[str, Any],
                            ttl: int = 7200) -> bool:
        """Cache post analytics."""
        return await self.set(f"analytics:{post_id}", analytics, ttl, 'analytics')

    async def get_cached_analytics(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics."""
        return await self.get(f"analytics:{post_id}", 'analytics')

    async def cache_user_preferences(self, user_id: str, preferences: Dict[str, Any],
                                   ttl: int = 86400) -> bool:
        """Cache user preferences."""
        return await self.set(f"preferences:{user_id}", preferences, ttl, 'users')

    async def get_cached_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user preferences."""
        return await self.get(f"preferences:{user_id}", 'users')

    # Utility methods

    def _get_full_key(self, key: str, namespace: str = None) -> str:
        """Get full key with namespace prefix."""
        if namespace and namespace in self.namespaces:
            return f"{self.namespaces[namespace]}{key}"
        elif namespace:
            return f"{namespace}:{key}"
        else:
            return key

    def _serialize(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError):
            # Fallback to pickle for complex objects
            return pickle.dumps(value).decode('latin1')

    def _deserialize(self, value: str) -> Any:
        """Deserialize value from Redis storage."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Try pickle deserialization
            try:
                return pickle.loads(value.encode('latin1'))
            except Exception:
                raise ValueError("Failed to deserialize cached value")

    def _update_hit_rate(self):
        """Update cache hit rate metric."""
        total_requests = self.metrics['hits'] + self.metrics['misses']
        if total_requests > 0:
            self.metrics['hit_rate'] = self.metrics['hits'] / total_requests

    async def _cleanup_expired_entries(self):
        """Background task to clean up expired entries from local cache."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes

                current_time = datetime.utcnow()
                expired_keys = []

                for key, entry in self._local_cache.items():
                    if entry.ttl and (current_time - entry.created_at).seconds > entry.ttl:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self._local_cache[key]

                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired local cache entries")

            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache manager metrics."""
        return dict(self.metrics)

    async def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        if not self.redis:
            return {}

        try:
            info = await self.redis.info('memory')
            return {
                'redis_memory_used': info.get('used_memory_human', 'unknown'),
                'redis_memory_peak': info.get('used_memory_peak_human', 'unknown'),
                'local_cache_entries': len(self._local_cache),
                'namespaces': list(self.namespaces.keys()),
                **self.metrics
            }
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {}
