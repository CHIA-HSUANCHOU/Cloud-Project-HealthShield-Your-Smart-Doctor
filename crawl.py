import requests
from pathlib import Path
import time
import random


BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{start}/DataFiles/{name}.xpt"

#MODULES = [
#    "DEMO", "BMX", "SMQ", "SLQ", "AL_IGE", "COT", "VID",
#    "PBCD", "UAS", "UHG", "RDQ", "SMQFAM","MCQ","PBCD",
#    "DIQ", "GLU", "TCHOL", "HDL", "TRIGLY", "BPX","ALQ", "PAQ", "HUQ", "GHB"
#]

MODULES = ["GHB"]


# 每個 Cycle 的設定： (folder_name, start_year, suffix)
cycles = [
    ("nhanes_19992000", 1999, None),
    ("nhanes_20012002", 2001, "B"),
    ("nhanes_20032004", 2003, "C"),
    ("nhanes_20052006", 2005, "D"),
    ("nhanes_20072008", 2007, "E"),
    ("nhanes_20092010", 2009, "F"),
    ("nhanes_20112012", 2011, "G"),
    ("nhanes_20132014", 2013, "H"),
    ("nhanes_20152016", 2015, "I"),
    ("nhanes_20172018", 2017, "J"),      # J cycle
    ("nhanes_20172020", 2017, "P"),      # P files only
    ("nhanes_20212023", 2021, "L"),      # L cycle
]
def url_exists(session: requests.Session, url: str, timeout=(10, 10)) -> bool:
    """先用 HEAD；若非 200 再用 GET 試探（避免部分站拒絕 HEAD）。"""
    try:
        r = session.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return True
        r = session.get(url, stream=True, timeout=timeout)
        return r.status_code == 200
    except requests.RequestException:
        return False

def download(session: requests.Session, url: str, dest: Path, timeout=(10, 300)) -> bool:
    """下載檔案並回傳是否成功。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"已存在，略過：{dest}")
        return True

    if not url_exists(session, url, timeout=(10, 10)):
        print(f"[不存在] {url}")
        return False

    print(f"下載 {url} -> {dest}")
    try:
        with session.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
        print(f"完成：{dest}")
        return True
    except Exception as e:
        print(f"[錯誤] {url} -> {e}")
        return False



def main():
    counter = 0

    with requests.Session() as session:
        session.headers.update({"User-Agent": "NHANES-downloader/1.0"})

        for folder_name, start, suffix in cycles:
            folder = Path(folder_name)
            if not folder.exists():
                print(f"資料夾不存在，略過：{folder}")
                continue
            
            print(f"\n=== Processing {folder_name} ===")

            for mod in MODULES:
                success = False
                # 1999–2000 沒字母
                if suffix is None:
                    fname = mod
                    url = BASE_URL.format(start=start, name=fname)
                    out = folder / f"{fname}.xpt"
                    success = download(session, url, out)

                # P cycle：檔名是 P_MOD
                elif suffix == "P":
                    fname = f"P_{mod}"
                    url = BASE_URL.format(start=start, name=fname)
                    out = folder / f"{fname}.xpt"
                    success = download(session, url, out)

                # 2017–2018：同時下載 J + P
                # J cycle：只下載 MOD_J.xpt
                elif suffix == "J":
                    fname = f"{mod}_J"
                    url = BASE_URL.format(start=start, name=fname)
                    success = download(session, url, folder / f"{fname}.xpt")

                # 一般 cycle mod_suffix
                else:
                    fname = f"{mod}_{suffix}"
                    url = BASE_URL.format(start=start, name=fname)
                    out = folder / f"{fname}.xpt"
                    success = download(session, url, out)

                # 隨機休息
                if success:
                    counter += 1
                    if counter % 5 == 0:
                        wait = round(random.uniform(2.5, 6.5), 2)
                        print(f"休息 {wait} 秒...")
                        time.sleep(wait)


if __name__ == "__main__":
    main()