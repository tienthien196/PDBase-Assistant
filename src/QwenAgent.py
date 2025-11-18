#!/usr/bin/env python3
"""
Tái tạo request chat.qwen.ai hoàn toàn giống capture
"""

import json
import requests
import uuid
import time

# ---------- CONFIG ----------
# ---------- CONFIG ----------
JWT          = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2ZDQ5YWVlLTQwYWQtNDNlYi1hMzc1LWVhNDdmMWRiMTIwYyIsImxhc3RfcGFzc3dvcmRfY2hhbmdlIjoxNzUwNjYwODczLCJleHAiOjE3NjQwNjE2NTl9.CQHGpiek0y0U59L1Aka42IXiIKyLjyLbJCTjrCooj1g"
CHAT_ID      = "74fd50b3-f1e4-4094-b8b9-01c44e448c18"   # Đúng rồi!
PARENT_ID    = "5a9eeeaf-3f3e-4a6e-b21b-16b487b177d8"   # ← Sửa tại đây!
USER_AGENT   = "Mozilla/5.0 ..."
BX_UA        = "231!AzB3l+mUypv+j3S+UA3G7MEjUq/YvqY2leOxacSC80vTPuB9lMZY9mRWFzrwLEV0PmcfY4rL2yQQzv4epFzCDXCN39IsbtzKjZV3BwK/R5DDDxuDiKaulHZWSpMXZKNwEGeLDZWdu3zSO4SgWJLtk51l/D+3mwP9WGB534u0uMwMpgca26uVzRCzNjqFp6pfHCRJsICPI0OXcqJdjcBc+fstyqP8G6361SO6KKpr+/nep4Dqk+I9xGdF5gci0HlCok+++4mWYi++6PXMo7V03U0DjDmnuOXMEuy19T1fHkZj9N/6HxcB/+/h3wh3awnVao2CJILN1i35g9SymtmD0ZVLjqJpoZ6qCBKW9kZjFe0N9VWA34iZ4SNz3k/tBOq2R1q2ZPYb370ZTMwDmoc+daxH95aJVkSrBy+5FB31XcJDV7g62GMSrMy0iqfBKqwS5hvvk4iNE3Zg2YEnXfWlPayVVWC3mScaLOrPRKF3+mumCD6nnULbj3mxyj7nEd1tgxCPeGgLiW/fBfUPuTotWVlBGJQEs8SKGkwRavovETFFLwMYLmQtbneGWUjBEsIvyeI5hmv85nsHMrhXbh4hNYd03kSIlM1MP1X4Cq44iWWS8PeBC/DV73u5a2afZc75Nubhh5vMDHyK66CHSjNR4xXXTnalcjWnsW3vo6wW2DFq78aiOV3nQNv7CDZYTPQBBP2oxJkcJgvCguC7C532DYaWYc+lTPrHtLm063Wg+h2C4VYcHZ29DhR/zXYkoGfiA3rb7K46MV4bkeeReNNTvq0O3Grv5byezYoQ9RxYGO4sQtmSW3cs9y4s407LPmcgoDWJfmZzEb07hUvpph/BSi2YLJg8MSxu5EL4NSxrKTJXb0J2OtYsixOVrWjFEf/guE/6cW2XFPozfVCMsVBWxUg0P7SpxTwC2G4fCVqPS1UPzHiJYZNemf9W9O7ZCGhVi/1kqoCwCrjh4OzntnUpZr09dAapgDbMhZanxl/RDi1BDLCrZYtqJBoNOx3Sk8Y3HBv0hYzjZIGh9pOZIOinpabKRcvz0nvN0qIkkF2SUPOzGMaNpkxz4KYaGy7eGlRAnHQyGkUFqvUKJ9o8kSZj/yIcMCuBvrKtoFlQuSU95XL7M4UV3A3Hh3aVf3rKB/vD9UKgQSD/kTkGE2309genAAY1xoR+ELc9GYvnVLOqXCczzOKLkSGVu13ZlnoEF7NXsHtUAJyRqulaG1ysSQ7f9io9S+J6YfbZ06JiLf/Xj/8p0z0rM++hTmWSgosMzotwFRdASoj45pQUmxZfpvokHD7iOMe2U5CF/hYzu1f+V/1+3OCxfplLdeBCmiyGvFVBl1ZBne0xep+BZvCCuB1i1zijxdfEHKXapsvQOQNpkne+LjEefLBic9kRkW9DvTHlB40/Uo9KDtHpSepnC5KM5bUt1VdZiMOD4yoaeDIXn33NEQ7J3R86aqbQO0ykT3InyspXggwxvA9Qqna2Rf733dQOZY3lcIsb7ovPjALhRvry4AF8o7wyIxAaH+d6Ix1Gn3u3CNpsh6LJbLxMu7JFZlyTzGlA0nZbI34n/TynamF1nyYMrldbSt0+3uNjjmfup6oBgFDnG/Zzi94OnNGg7t1UGkPeqqtSFZtpJ1hTAku16Ga2wDVsO4=="
BX_UMIDTOKEN = "T2gAYlC44JuCIkVN-Bz8W7-yYESU8pSsEj21dulNP0huUFHjq7FwaopoYe04A-SRNqE="
# ---------- COOKIE ----------
COOKIE_RAW = (
    "cna=taRNIL78HkgCATq6MFcYSPOb; "
    "visitor_id=ef774ac6e22316d4da1182628e661228; "
    "cnaui=422280e6-4d77-4264-9fb8-855f3a2b2bf3; "
    "aui=422280e6-4d77-4264-9fb8-855f3a2b2bf3; "
    "_gcl_au=1.1.1328138642.1756634692; "
    "_bl_uid=sgmq1fg7aeXzCdo7tb0zgsCpd4Lk; "
    "xlly_s=1; "
    "x-ap=ap-southeast-1; "
    "sca=fe31cdb3; "
    f"token={JWT}; "
    "atpsida=60258e5ad0c71d6175d1f050_1759653958_5; "
    "acw_tc=0a03e54a17596542666607262e1e86d212d0610a7c6baf0a573e6608dd3362; "
    "tfstk=gMsxlmGs57VmGmcqH14ujBZPA8ellzX4NsWIjCAm5_CR1swqjOTm1cCJZ-WDcS5JFKvASCwwGFIJC17ictO6Xcp2wRJb_5S-N6vshNVwhhhWd1316Oy2CC116Cb0rkXV3h-_tCE3xtSMWJ-PMCt6NR9ppqwklobHFIt_tWqu0z3Vqh1gLciXFTOyBdG6f1OWVpJpfd9Xf8dWBpusG1t_e8p6QC9scEGSNp9MfC16C8LWKQ9XfF11F8pwNCMwxxdihCnOlY2dykHQx8eR2KLv6q4nYDq1HXYNhumnvgQRZBZHwci12KB9CRrxvPAC8IYHT_ZoDhBWB_LhkWnA6O6F5UItG-fCCsSJ0HUg3eQ5rwYAySi9Ziv9RhT-Cc6J2Q5dqHZIwL75nNsVMAn63ijHWB88Cc8MVMYCRsHaLTtXC18FjWo2GO6FYwxLDXJAP9KR4oshvpKjtBpil8e-7V8XUr9yE2SgvAP6eB2orVuwrLJJt8e-7V8XULd3Eu0Z7UvP.; "
    "isg=BP7-LOPOGku8REFLbsGBdBDKTxRAP8K58Rr1dKgnJ85CS6kmq86By6ttww-H87rR; "
    "ssxmod_itna=1-CqGxuDnDcD2GlDeKqmq0K3uDek0DRlxBP01Dp6xQ5DODLxnR5GdKR8L_i3H3KWKFKixDtgKtCitDl2ihYD9xY6HDj4GT_zhBqhCxonAxuN4OmLvPpq6GiEpy35QBwb4cO9kA8d30qW=qEOHHWY4DHPPDUO0Yx34DxOPD5xDTDWeDGDD3DmW_DivoD0KDjGEvh3fIDYPDEC3DRPa3j/3D7O4Ib4keDD5DAPPDwpRIeDDzeAQxY72wFl3DePPjIYlvKe=qQGgTED0H3l=x79dB_TGErvZ96fmmDlKlDCIAgSE0Rjofw9fYsnKD3_Ulh_n5=0GhixeCD9mq4lqPGDm7D4tDQmh442CY4eGDt9PDDcq=u9/HHzGPerlAvZta_RvY3bGUuGfwYQ0CjD7jDb3ew3mtB2tR0imAYY3kIw4KxxEGDD; "
    "ssxmod_itna2=1-CqGxuDnDcD2GlDeKqmq0K3uDek0DRlxBP01Dp6xQ5DODLxnR5GdKR8L_i3H3KWKFKixDtgKtCGYDioR_4rqiQe03QY7OSvqqWQ04D/04OfxPsVQp8gXefR7SwXXDpPxOu2QWvQ4gszVh4yov766FQO=p4Gc9kGQnHXrxOQeE_q_9mF7GpAO0iIcYCityWp/xAaF8EFlxkISBrRZFEoQdj0rhC4/_z9Kw1XGGzYBSdHDd4K_5qQicCW=CpsihGsWDssOGaOxnG7AA198vGeoymXPyC6cdCKd7k3i0j4Sdv2n9Ru_phZxCaq3KT8Dxlq9hk53TqROM2F8odXO=x3d7E78uT/RQwoeOMP=YOyO=5xFWiCZhxsQKqx=FWxAO1enh0f_XuW7gitDFZMCSEHeu7td7d4tf8kjqx_OYSSPeCQ2E=ArqSRD=1vClqynQTQxq8DSODzbwn2LOMrToYsuHzSm9rCGOb62_Axfqgm7E1LhkY8=ZQ1mS=6gYd6vrcDyq0aOxXfWOBFpb3M8YZj5lO7u_DWhjkTtYiCckzuhGKmQKw3Vok=fzG289db_uHTMc0OzsR1m9cOO6vE3fO0AgnK073ddcu7CZq/8EgWCGI3rWa=pQ59Wz4neFS/hSWbtZnH/MpEqNlfz3HMFOEXe9OvE1mF2ja_0G3Bo=L3HMILj35Yb62LX24wW0osrRkBa6xDbi4xV=PGcxtsU2DiGQBqge4buQNCqY7x_qOhDWGiDKcvKFNGa8ehOBcAKF0=rD7Awm_m23zF77C1DvcqSDYDH0ocvRA5aBWlh_0FixS_uDoeGK6hjxmhbrYxlWU4xWo=qVOp67mYp7ALGbh4qeer472mKitieW0i_IxyOfql0tmxG44Y4P2i7xoEYQsyOCbD4D"
)
COOKIE_RAW = "cna=PSB1IO4VdD8CAQE2j54d+B9m; cnaui=66d49aee-40ad-43eb-a375-ea47f1db120c; aui=66d49aee-40ad-43eb-a375-ea47f1db120c; _bl_uid=j1mjkgRnc3m80R4tzs23e9LhdgmF; _gcl_au=1.1.1232082033.1762146553; xlly_s=1; acw_tc=0a03e59517634568475047093e0f38e76819e03a0321daa4fbbb552c265871; x-ap=ap-southeast-1; sca=466826a6; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2ZDQ5YWVlLTQwYWQtNDNlYi1hMzc1LWVhNDdmMWRiMTIwYyIsImxhc3RfcGFzc3dvcmRfY2hhbmdlIjoxNzUwNjYwODczLCJleHAiOjE3NjQwNjE2NTl9.CQHGpiek0y0U59L1Aka42IXiIKyLjyLbJCTjrCooj1g; atpsida=2830e4b6afa9c3093ec14eb1_1763457530_4; tfstk=g6eS-IXpvUY7BDNtNvS21ctxo8DI2iWwyHiLjkpyvYH-RHaUXXnyUgVQGyzSy8kJemdQScgdx4EJOxUZXbpKpQnYhyiRx3E-px3IjcFyp2pKRxnoeXVr84uIdk410NWNQuqoKXQN7O5x9U8nILdKpeRvkcMI29eTpCEoKvQVrWIanu4rMHIK9vIjHDiJpvdJeKIjAcd-p4hpkIntk2HLJXBxD0mM92dJwIIjxqp-pvUKHiiEk2HKpyExIs7jm_g8VGVauxrCdONslppLhmIubuOMhDyEVTg_4q1dt-9iNVE-lpQG-Y0iRq2OusZ077Urmy61lAFglJGtdTTiVSEsH4kOF30TUDZaOl_68mV8P-hQ3MfucJgS68hXXpkxnDUKOSb6Q0MzGfw7ZMYY2Pu76Yqefarj1SGiDjKBwYPabJcTeTTiufmQlfP55LaO4j9Z5SxJOnGMdmgNciOHtigN0KbGjvnswmm4QisXPBc-mmgNciOHtbnm0fSfcUOh.; isg=BPb2LA9Dg12GiXlLonFgCTiMRyz4FzpRKULtXGDZGFh0o5k9mqbiY_gVu2fPPzJp; ssxmod_itna=1-eqjxBDRD0DcDn77qi7qit9o0QfPYKiOeDzxC5A50CDmxjKidYDUDQwlGuSBD0=ent7CGhP8nY2Dx61DBkDwrDjqi8XD7PDvKZR2_1eBcBgDvYBOO0tK5O8GGqvhgczDOPQXVmIh9e7BC=4AT0MW7mpDBfED0=8iBLrDYYjDBYD74G_DDeDixGmFeDSDxD9DGP=x1WbgeDEDYpWxiUEb2c7xDdinmbOvDDBDD6ED7jWSWxD0TxIa0x4_mG7xGAEmPe_qpIELTuAbxGX7DCPnly05HxWvzMSzpo3xB6BxBQbyPW_pETadZcriDC4BYQe4Q0Y/uDA2DQGPCG4t_q9h43RqQDNArxZxKKGxEBtKxobwhDDWTQ=cxGKRxt8eRLzydadbswBGPDNBji5_5YGD=BDvO5DO5/DYQ053DxLgre24XhvohGDn44D; ssxmod_itna2=1-eqjxBDRD0DcDn77qi7qit9o0QfPYKiOeDzxC5A50CDmxjKidYDUDQwlGuSBD0=ent7CGhP8nY2Dx6rDG8mb4FKgixNDLACGa45BgqDs2i7=KqLn7e/4gxntv/pw2X019rBmma/tQ4dSc4=cn_tyDb6g3GNSU_UVelP47Tx/YWLxK0GXCG62Gl5RCGT5KYQ4blrBFwtM4wT3hWdNaAX6j_fXnS2MUf6uYBduQwGbs2DLGau4r/Qe4MN7hkQ3Na=9jbA0CwagnFNLQGICOIKPDzQ64suu8ZXWV_IViB7xgg7Y8px3riLUr7QoaNI=DPC5FZ4uBDdlQROie0onjAPCdYf3uiwLCYwOP49fHnd3gD22fDE3IxIqFRXQ5thDzBQ8CQezK2aGg0DSpKCQv_0vAefQz5oPo/0ENSTRm2niEOf2gQrxrA5Rv5/5i6DKmI02rPQKZ6RUUPGjPYQDa1uiFjz3IC_5O8DtaDzWL7CLP_iuG0G_Yw/DofAYP6xpHwBrrRID4v/zdvPvLc=IzEQxNOKAMmE2iPf434C2dTwn2vwrEd7bfcBE6Y6ioCtbiNIVxtQPKzlvjzK8Z_B1IDcBzGPqO0Yzmsg3trD7pMRZK8fIFI2brSBbwKq2ITv2D1cCjxBE_avt48lG=Kk=bHDusK=rSkEC9aU2qrq8MyQpPBG1Ap5m00IcC28giZCwggRnXDQICqCSV0_dbVf=UYHmpKn3Bx8Ew0xg2dj4di10etbh04=e4F07bdB_jLGIvYWZAIThLji7xg94sDd4_alYAK8mq5xPDYtmz0OS3uRO3GPfGRPBSdb28fMevzn4iGjfIQD8EG_tz0oXwU34VXUWxj0GCD9hAG5du9DVShsYYlhU_xAUvYVS3E0j9xKG5PD"

# ---------- BUILD HEADERS ----------
HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
    "authorization": f"Bearer {JWT}",
    "bx-ua": BX_UA,
    "bx-umidtoken": BX_UMIDTOKEN,
    "bx-v": "2.5.31",
    "connection": "keep-alive",
    "content-type": "application/json; charset=UTF-8",
    "cookie": COOKIE_RAW,
    "host": "chat.qwen.ai",
    "origin": "https://chat.qwen.ai",
    "referer": f"https://chat.qwen.ai/c/{CHAT_ID}",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "source": "web",
    "timezone": "Sun Oct 05 2025 16:19:51 GMT+0700",
    "user-agent": USER_AGENT,
    "version": "0.0.221",
    # "x-request-id": "74fd50b3-f1e4-4094-b8b9-01c44e448c18"
}

# --------------- AGENT ---------------
class QwenAgent:
    """
    Agent tương tác với chat.qwen.ai – giữ nguyên mọi const ở trên
    """
    def __init__(self,
                 jwt: str = JWT,
                 chat_id: str = CHAT_ID,
                 parent_id: str = PARENT_ID) -> None:
        self.jwt = jwt
        self.chat_id = chat_id
        self.parent_id = parent_id
        self.url = f"https://chat.qwen.ai/api/v2/chat/completions?chat_id={self.chat_id}"

        # headers – clone y hệt capture
        self.headers = HEADERS.copy()
        self.headers["authorization"] = f"Bearer {self.jwt}"

    # --------------- CORE ---------------
    def send(self, content: str, stream: bool = True) -> requests.Response:
        """Gửi tin nhắn và trả về object Response đã stream=True"""
        fid = str(uuid.uuid4())
        payload = {
            "stream": stream,
            "incremental_output": True,
            "chat_id": self.chat_id,
            "chat_mode": "normal",
            "model": "qwen3-max-2025-10-30",
            "parent_id": self.parent_id,
            "messages": [
                {
                    "fid": fid,
                    "parentId": self.parent_id,
                    "childrenIds": [str(uuid.uuid4())],  # placeholder
                    "role": "user",
                    "content": content,
                    "user_action": "chat",
                    "files": [],
                    "timestamp": int(time.time()),
                    "models": ["qwen3-max"],
                    "chat_type": "t2t",
                    "feature_config": {
                        "thinking_enabled": False,
                        "output_schema": "phase"
                    },
                    "extra": {"meta": {"subChatType": "t2t"}},
                    "sub_chat_type": "t2t"
                }
            ],
            "timestamp": int(time.time())
        }

        return requests.post(self.url, headers=self.headers, json=payload, stream=stream)

    # --------------- UTILS ---------------
    def stream_print(self, content: str) -> None:
        """Gửi và in luôn từng chunk SSE"""
        with self.send(content, stream=True) as resp:
            print("HTTP", resp.status_code, resp.reason)
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    print(line)


# --------------- DEMO ---------------
if __name__ == "__main__":
    agent = QwenAgent()
    agent.stream_print("bạn có biết code godot không, dùng multiplayer API của godot 3")

