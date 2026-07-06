from __future__ import annotations

import ctypes


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class _PerformanceInformation(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("CommitTotal", ctypes.c_size_t),
        ("CommitLimit", ctypes.c_size_t),
        ("CommitPeak", ctypes.c_size_t),
        ("PhysicalTotal", ctypes.c_size_t),
        ("PhysicalAvailable", ctypes.c_size_t),
        ("SystemCache", ctypes.c_size_t),
        ("KernelTotal", ctypes.c_size_t),
        ("KernelPaged", ctypes.c_size_t),
        ("KernelNonpaged", ctypes.c_size_t),
        ("PageSize", ctypes.c_size_t),
        ("HandleCount", ctypes.c_ulong),
        ("ProcessCount", ctypes.c_ulong),
        ("ThreadCount", ctypes.c_ulong),
    ]


def sample_commit_cache_pool() -> dict:
    fallbacks: list[str] = []
    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(status)
    ok_status = False
    try:
        ok_status = bool(ctypes.WinDLL("kernel32.dll").GlobalMemoryStatusEx(ctypes.byref(status)))
    except Exception:  # noqa: BLE001
        fallbacks.append("GlobalMemoryStatusEx_unavailable")
    perf = _PerformanceInformation()
    perf.cb = ctypes.sizeof(perf)
    ok_perf = False
    try:
        psapi = ctypes.WinDLL("psapi.dll")
        psapi.GetPerformanceInfo.argtypes = [ctypes.POINTER(_PerformanceInformation), ctypes.c_ulong]
        psapi.GetPerformanceInfo.restype = ctypes.c_int
        ok_perf = bool(psapi.GetPerformanceInfo(ctypes.byref(perf), perf.cb))
    except Exception:  # noqa: BLE001
        fallbacks.append("GetPerformanceInfo_unavailable")
    page = perf.PageSize if ok_perf and perf.PageSize else 4096
    total_phys = _bytes_to_mb(status.ullTotalPhys) if ok_status else _pages_to_mb(perf.PhysicalTotal, page)
    avail_phys = _bytes_to_mb(status.ullAvailPhys) if ok_status else _pages_to_mb(perf.PhysicalAvailable, page)
    commit_total = _pages_to_mb(perf.CommitTotal, page) if ok_perf else _bytes_to_mb(status.ullTotalPageFile - status.ullAvailPageFile)
    commit_limit = _pages_to_mb(perf.CommitLimit, page) if ok_perf else _bytes_to_mb(status.ullTotalPageFile)
    cache = _pages_to_mb(perf.SystemCache, page) if ok_perf else None
    paged = _pages_to_mb(perf.KernelPaged, page) if ok_perf else None
    nonpaged = _pages_to_mb(perf.KernelNonpaged, page) if ok_perf else None
    used = max(0.0, total_phys - avail_phys)
    return {
        "total_physical_mb": round(total_phys, 3),
        "available_physical_mb": round(avail_phys, 3),
        "used_physical_mb": round(used, 3),
        "commit_total_mb": round(commit_total, 3),
        "commit_limit_mb": round(commit_limit, 3),
        "commit_used_percent": round((commit_total / commit_limit * 100.0) if commit_limit else 0.0, 3),
        "cache_bytes_mb": round(cache, 3) if cache is not None else None,
        "standby_cache_mb": None,
        "modified_page_list_mb": None,
        "paged_pool_mb": round(paged, 3) if paged is not None else None,
        "nonpaged_pool_mb": round(nonpaged, 3) if nonpaged is not None else None,
        "memory_compression_mb": None,
        "pagefile_usage_mb": round(commit_total, 3),
        "sampler_fallbacks_used": fallbacks,
    }


def _bytes_to_mb(value: int | float) -> float:
    return float(value) / (1024 * 1024)


def _pages_to_mb(pages: int | float, page_size: int | float) -> float:
    return float(pages) * float(page_size) / (1024 * 1024)
