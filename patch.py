import re

with open("/app/extractors/vixsrc.py", "r", encoding="utf-8") as f:
    src = f.read()

# In _make_robust_request, after curl_cffi fallback fails in the 403 handler,
# inject a FlareSolverr fallback before raising the final error.
old = """            if e.status == 403:
                    try:
                        logger.info("aiohttp 403 detected, trying curl_cffi for %s", url)
                        headers_403 = final_headers or self._default_headers()
                        return await self._make_curl_request(url, headers=headers_403, forced_proxy=forced_proxy)
                    except Exception as cffi_exc:
                        logger.warning("curl_cffi fallback failed for %s: %s", url, cffi_exc)

                if attempt == retries - 1:"""

new = """            if e.status == 403:
                    try:
                        logger.info("aiohttp 403 detected, trying curl_cffi for %s", url)
                        headers_403 = final_headers or self._default_headers()
                        return await self._make_curl_request(url, headers=headers_403, forced_proxy=forced_proxy)
                    except Exception as cffi_exc:
                        logger.warning("curl_cffi fallback failed for %s: %s", url, cffi_exc)
                        try:
                            logger.info("curl_cffi failed, trying FlareSolverr for %s", url)
                            return await self._make_flaresolverr_request(url, headers=final_headers, forced_proxy=forced_proxy)
                        except Exception as fs_exc:
                            logger.warning("FlareSolverr fallback also failed for %s: %s", url, fs_exc)

                if attempt == retries - 1:"""

if old not in src:
    print("ERROR: pattern 403 not found")
else:
    src = src.replace(old, new)
    print("Patched 403 handler in _make_robust_request")

# Also patch _resolve_embed_url_from_api to add FlareSolverr fallback
# after curl_cffi fails and before the final error
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
                logger.warning("robust failed, trying FlareSolverr for API: %s", robust_err)
                try:
                    response = await self._make_flaresolverr_request(api_url, headers=api_headers, forced_proxy=forced_proxy)
                except Exception as fs_err:
                    raise ExtractorError(f"VixSrc API fetch failed: {fs_err}") from fs_err"""

if old2 not in src:
    print("ERROR: pattern _resolve_embed_url_from_api not found")
else:
    src = src.replace(old2, new2)
    print("Patched _resolve_embed_url_from_api with FlareSolverr fallback")

with open("/app/extractors/vixsrc.py", "w", encoding="utf-8") as f:
    f.write(src)

print("Patch complete")
