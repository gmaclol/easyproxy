import re

with open("/app/extractors/vixsrc.py", "r", encoding="utf-8") as f:
    src = f.read()

# In _make_robust_request 403 handler: after curl_cffi fails,
# use _ensure_cookies to get fresh cf_clearance from FlareSolverr,
# then retry curl_cffi.
old = """            if e.status == 403:
                    try:
                        logger.info("aiohttp 403 detected, trying curl_cffi for %s", url)
                        headers_403 = final_headers or self._default_headers()
                        return await self._make_curl_request(url, headers=headers_403, forced_proxy=forced_proxy)
                    except Exception as cffi_exc:
                        logger.warning("curl_cffi fallback failed for %s: %s", url, cffi_exc)"""

new = """            if e.status == 403:
                    try:
                        logger.info("aiohttp 403 detected, trying curl_cffi for %s", url)
                        headers_403 = final_headers or self._default_headers()
                        return await self._make_curl_request(url, headers=headers_403, forced_proxy=forced_proxy)
                    except Exception as cffi_exc:
                        logger.warning("curl_cffi fallback failed for %s: %s", url, cffi_exc)
                        try:
                            logger.info("Refreshing cookies via FlareSolverr for %s", url)
                            await self._ensure_cookies(url, force_refresh=True)
                            fresh_headers = self._fresh_headers()
                            fresh_headers.pop("User-Agent", None)
                            fresh_headers.pop("user-agent", None)
                            logger.info("Retrying curl_cffi with fresh FlareSolverr cookies for %s", url)
                            return await self._make_curl_request(url, headers=fresh_headers, forced_proxy=forced_proxy)
                        except Exception as fs_retry_exc:
                            logger.warning("FlareSolverr cookie refresh + retry also failed for %s: %s", url, fs_retry_exc)"""

if old not in src:
    print("ERROR: pattern 403 not found")
else:
    src = src.replace(old, new)
    print("Patched 403 handler in _make_robust_request")

# In _resolve_embed_url_from_api: after curl_cffi + robust fail,
# refresh cookies via FlareSolverr and retry curl_cffi.
old2 = """        try:
            logger.info("Trying VixSrc API via curl_cffi proxy rotation: %s", api_url)
            response = await self._make_curl_request(api_url, headers=api_headers, forced_proxy=forced_proxy)
        except Exception as curl_err:
            # 404 means content not found — FS won't help, skip cascading fallbacks
            if "404" in str(curl_err):
                raise ExtractorError(f"VixSrc API endpoint not found (404): {api_url}")
            logger.warning("curl_cffi failed for API, trying robust: %s", curl_err)
            try:
                response = await self._make_robust_request(api_url, headers=api_headers, forced_proxy=None)
            except Exception as robust_err:
                if "404" in str(robust_err):
                    raise ExtractorError(f"VixSrc content not found (404): {api_url}")
                raise ExtractorError(f"VixSrc API fetch failed: {robust_err}") from robust_err"""

new2 = """        try:
            logger.info("Trying VixSrc API via curl_cffi proxy rotation: %s", api_url)
            response = await self._make_curl_request(api_url, headers=api_headers, forced_proxy=forced_proxy)
        except Exception as curl_err:
            if "404" in str(curl_err):
                raise ExtractorError(f"VixSrc API endpoint not found (404): {api_url}")
            logger.warning("curl_cffi failed for API, trying robust: %s", curl_err)
            try:
                response = await self._make_robust_request(api_url, headers=api_headers, forced_proxy=None)
            except Exception as robust_err:
                if "404" in str(robust_err):
                    raise ExtractorError(f"VixSrc content not found (404): {api_url}")
                logger.warning("robust failed, trying FlareSolverr cookie refresh + curl_cffi for API: %s", robust_err)
                try:
                    logger.info("Refreshing cookies via FlareSolverr for API %s", api_url)
                    await self._ensure_cookies(api_url, force_refresh=True)
                    fresh_headers = {**api_headers}
                    fresh_headers.pop("User-Agent", None)
                    fresh_headers.pop("user-agent", None)
                    logger.info("Retrying curl_cffi with fresh FlareSolverr cookies for API %s", api_url)
                    response = await self._make_curl_request(api_url, headers=fresh_headers, forced_proxy=forced_proxy)
                except Exception as fs_err:
                    raise ExtractorError(f"VixSrc API fetch failed: {fs_err}") from fs_err"""

if old2 not in src:
    print("ERROR: pattern _resolve_embed_url_from_api not found")
else:
    src = src.replace(old2, new2)
    print("Patched _resolve_embed_url_from_api with FlareSolverr fallback")

# Also patch the embed fallback in extract() after _resolve_embed_url_from_api:
# when curl_cffi fails for the embed URL, add a FlareSolverr refresh + retry
old3 = """                        try:
                            response = await self._make_robust_request(
                                embed_url,
                                headers=self._fresh_headers(referer=url),
                                forced_proxy=None,
                            )
                        except Exception as robust_err:
                            raise ExtractorError(f"VixSrc embed fetch failed: {robust_err}") from robust_err"""

new3 = """                        try:
                            response = await self._make_robust_request(
                                embed_url,
                                headers=self._fresh_headers(referer=url),
                                forced_proxy=None,
                            )
                        except Exception as robust_err:
                            logger.warning("robust failed for embed, trying FlareSolverr refresh + curl_cffi: %s", robust_err)
                            try:
                                await self._ensure_cookies(embed_url, force_refresh=True)
                                fresh_headers_embed = self._fresh_headers(referer=url)
                                fresh_headers_embed.pop("User-Agent", None)
                                fresh_headers_embed.pop("user-agent", None)
                                response = await self._make_curl_request(embed_url, headers=fresh_headers_embed, forced_proxy=forced_proxy)
                            except Exception as fs_embed_err:
                                raise ExtractorError(f"VixSrc embed fetch failed: {fs_embed_err}") from fs_embed_err"""

if old3 not in src:
    print("ERROR: pattern embed fallback not found")
else:
    src = src.replace(old3, new3)
    print("Patched embed fallback in extract()")

with open("/app/extractors/vixsrc.py", "w", encoding="utf-8") as f:
    f.write(src)

print("Patch complete")
