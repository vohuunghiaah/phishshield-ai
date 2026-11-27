"""Exercise the running loopback API with inert example.org data; persist HTTP evidence."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

import requests
import numpy as np
from phishshield.inference.service import predict

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",default="http://127.0.0.1:8000")
    base=parser.parse_args().base.rstrip("/")
    if urlsplit(base).hostname not in ("localhost","127.0.0.1","::1"):
        raise ValueError("Local service required")
    rows=[]
    def request(method,path,expected,payload=None,**kwargs):
        r=requests.request(method,base+path,json=payload,timeout=40,**kwargs)
        assert r.status_code==expected,(path,r.status_code,r.text[:200])
        body=r.json() if "application/json" in r.headers.get("content-type","") else {"title":"Swagger UI","bytes":len(r.content)}
        rows.append(dict(method=method,path=path,input=(payload if len(str(payload))<2048 else {"html_bytes":len(payload["html"])}),
                         status=r.status_code,response=body))
        return body
    request("GET","/health",200); request("GET","/ready",200);request("GET","/docs",200)
    info=request("GET","/model/info",200)
    snapshot="<html><title>Example</title><p>Local fixture</p><script type='text/plain'>inert</script></html>"
    url="https://example.org/"
    for html,role in [(None,"url_fallback"),(snapshot,"primary")]:
        payload={"url":url,**({"html":html} if html else {})}
        result=request("POST","/predict",200,payload)
        direct=predict(ROOT,url,html,"snapshot" if html else "disabled")
        for key in ("model_version","feature_modality","html_extraction_status","threshold","prediction"):
            assert result[key]==direct[key],key
        np.testing.assert_allclose(result["phishing_probability"],direct["phishing_probability"],rtol=0,atol=1e-12)
        for a,b in zip(result["explanation"]["contributions"],direct["explanation"]["contributions"],strict=True):
            assert a["feature"]==b["feature"] and a["value"]==b["value"]
            np.testing.assert_allclose(a["contribution"],b["contribution"],rtol=0,atol=1e-12)
        assert result["threshold"]==info[role]["threshold"] and result["feature_count"]==info[role]["feature_count"]
        assert result["prediction"]==int(result["phishing_probability"]>=result["threshold"])
    request("POST","/predict-from-html",200,{"url":url,"html":snapshot})
    request("POST","/explain",200,{"url":url,"html":snapshot})
    for payload in ({"url":""},{"url":"invalid"},{"url":url,"html":"  "}):
        request("POST","/predict",422,payload)
    request("POST","/predict",413,{"url":url,"html":"a"*(8388608+1)})
    request("POST","/predict",422,data=b"{",headers={"Content-Type":"application/json"})
    perf=request("GET","/performance",200)
    assert perf["metrics"]==json.loads((ROOT/"results/metrics/locked_test.json").read_text("utf8"))["metrics"]
    dest=ROOT/"reports/product/http_evidence.json"
    dest.parent.mkdir(exist_ok=True, parents=True)
    dest.write_text(json.dumps(rows,ensure_ascii=False,indent=2),"utf8")
    print(f"{len(rows)} HTTP checks passed")


if __name__=="__main__":
    main()

