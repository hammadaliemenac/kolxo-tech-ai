from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, re
import time
import collections

router = APIRouter()

def fetch_page(url):
    start = time.time()
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        return res, round(time.time() - start, 2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def make_ch(name, priority, status, msg, val=""):
    return {"name": name, "priority": priority, "status": status, "message": msg, "value": str(val)}

def calc_score(checks):
    if not checks: return 100
    pts = 0
    total = len(checks) * 2
    for c in checks:
        if c["status"] == "pass": pts += 2
        elif c["status"] == "warning": pts += 1
    return int((pts / total) * 100)

# --- CATEGORIES --- #
def chk_meta(soup, url, res):
    c = []
    
    # Title
    t = soup.title.string.strip() if soup.title and soup.title.string else ""
    if not t:
        c.append(make_ch("Title Tag", "critical", "fail", "Missing title tag."))
    elif len(t) < 30 or len(t) > 60:
        c.append(make_ch("Title Tag", "high", "warning", f"Title length ({len(t)}) sub-optimal (30-60).", t))
    else:
        c.append(make_ch("Title Tag", "medium", "pass", "Optimal title length.", t))
        
    t_words = set(t.lower().split())
    if len(t_words) != len(t.lower().split()):
        c.append(make_ch("Title Duplicates", "medium", "warning", "Title contains duplicate words.", t))
        
    # Meta Description
    desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    if not desc:
        c.append(make_ch("Meta Description", "critical", "fail", "Missing meta description."))
    elif len(desc) < 50 or len(desc) > 160:
        c.append(make_ch("Meta Description", "high", "warning", f"Length ({len(desc)}) sub-optimal (50-160).", desc))
    else:
        c.append(make_ch("Meta Description", "medium", "pass", "Optimal description length.", desc))

    # Crawlability
    robots = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if robots and "noindex" in robots.get("content", "").lower():
        c.append(make_ch("Crawlability", "critical", "fail", "Site blocked from indexing (noindex)."))
    else:
        c.append(make_ch("Crawlability", "critical", "pass", "Site allows indexing."))

    # Canonical
    can = soup.find("link", rel="canonical")
    if can: c.append(make_ch("Canonical Link", "high", "pass", "Canonical link defined.", can.get("href")))
    else: c.append(make_ch("Canonical Link", "high", "warning", "No canonical link."))

    # Language
    lang = soup.find("html").get("lang") if soup.find("html") else None
    if lang: c.append(make_ch("HTML Language", "low", "pass", "Language specified.", lang))
    else: c.append(make_ch("HTML Language", "low", "warning", "Language not specified."))

    # Pagination
    nex = soup.find("link", rel="next")
    pre = soup.find("link", rel="prev")
    c.append(make_ch("Pagination Tags", "low", "pass" if (nex or pre) else "warning", "rel=next/prev tags" + (" present." if nex or pre else " absent.")))

    # Doctype & Charset
    charset = soup.find("meta", charset=True)
    c.append(make_ch("Charset", "low", "pass" if charset else "warning", "UTF-8 Charset " + ("defined." if charset else "missing.")))
    
    # Favicon
    fav = soup.find("link", rel=lambda x: x and "icon" in x.lower())
    c.append(make_ch("Favicon", "low", "pass" if fav else "warning", "Favicon " + ("linked." if fav else "missing.")))

    return {"category": "Meta Data", "score": calc_score(c), "checks": c, "title": t}

def chk_quality(soup, t):
    c = []
    text = soup.get_text(separator=' ', strip=True)
    words = text.split()
    wc = len(words)
    
    # Word count & placeholder
    if wc < 300: c.append(make_ch("Word Count", "medium", "warning", f"Low word count ({wc})."))
    else: c.append(make_ch("Word Count", "medium", "pass", f"Good word count ({wc})."))

    if "lorem ipsum" in text.lower():
        c.append(make_ch("Placeholder Text", "critical", "fail", "Lorem Ipsum detected."))
    else:
        c.append(make_ch("Placeholder Text", "low", "pass", "No placeholders detected."))

    # Title match
    t_w = [w.lower() for w in t.split() if len(w) > 3]
    miss = [w for w in t_w if w not in text.lower()]
    if miss: c.append(make_ch("Title Match", "high", "warning", "Title words missing in content.", ", ".join(miss)))
    elif t_w: c.append(make_ch("Title Match", "medium", "pass", "Title keywords found in body."))

    # Paragraphs & Sentences
    ps = soup.find_all("p")
    c.append(make_ch("Paragraphs", "low", "pass" if len(ps) > 3 else "warning", f"{len(ps)} text blocks found."))
    
    sentences = re.split(r'[.!?]+', text)
    avg_s = wc / max(len(sentences), 1)
    if avg_s > 25: c.append(make_ch("Sentence Length", "low", "warning", "Sentences are too long on average.", f"{avg_s:.1f} words"))
    else: c.append(make_ch("Sentence Length", "low", "pass", "Good average sentence length.", f"{avg_s:.1f} words"))

    # Mobile
    vp = soup.find("meta", attrs={"name": "viewport"})
    c.append(make_ch("Viewport", "high", "pass" if vp else "fail", "Viewport meta " + ("present." if vp else "missing.")))
    
    apple = soup.find("link", rel="apple-touch-icon")
    c.append(make_ch("Apple Touch Icon", "low", "pass" if apple else "warning", "Apple Touch Icon " + ("found." if apple else "missing.")))

    # Tags
    strongs = soup.find_all(["strong", "b"])
    if len(strongs) > 30: c.append(make_ch("Strong/Bold Tags", "low", "warning", f"Too many bold tags ({len(strongs)}). Keep under 30."))
    else: c.append(make_ch("Strong/Bold Tags", "low", "pass", f"Reasonable bold tag count ({len(strongs)})."))

    # Images
    imgs = soup.find_all("img")
    no_alt = [i for i in imgs if not i.get("alt")]
    if no_alt: c.append(make_ch("Image ALT", "medium", "warning", f"{len(no_alt)} images missing ALT text."))
    else: c.append(make_ch("Image ALT", "medium", "pass", "All images have ALT text."))

    return {"category": "Page Quality", "score": calc_score(c), "checks": c}

def chk_others(soup):
    c = []
    # H1
    h1 = soup.find_all("h1")
    if not h1: c.append(make_ch("H1 Heading", "critical", "fail", "No H1 heading found."))
    elif len(h1) > 1: c.append(make_ch("H1 Heading", "high", "warning", f"Multiple H1 headings ({len(h1)})."))
    else: c.append(make_ch("H1 Heading", "high", "pass", "Perfect single H1 heading.", h1[0].text[:40]))

    # Duplicate H's
    heads = collections.Counter([h.text.strip().lower() for h in soup.find_all(["h1", "h2", "h3"])])
    dupes = [k for k, v in heads.items() if v > 1 and len(k)>3]
    if dupes: c.append(make_ch("Heading Duplicates", "high", "warning", "Duplicate heading texts found.", len(dupes)))
    else: c.append(make_ch("Heading Duplicates", "low", "pass", "No duplicate headings."))

    schema = soup.find("script", type="application/ld+json")
    c.append(make_ch("Schema.org", "low", "pass" if schema else "warning", "Structured data " + ("found." if schema else "missing.")))

    return {"category": "Headings & Extras", "score": calc_score(c), "checks": c}

def chk_links(soup, url):
    c = []
    dom = urlparse(url).netloc
    a = soup.find_all("a")
    i, e = 0, 0
    for l in a:
        h = l.get("href", "")
        if h.startswith("http") and dom not in h: e += 1
        elif h and not h.startswith("#") and not h.startswith("javascript"): i += 1

    c.append(make_ch("Internal Links", "high", "pass" if i > 0 else "warning", f"{i} internal links."))
    c.append(make_ch("External Links", "medium", "pass" if e > 0 else "warning", f"{e} external links."))
    
    lt = [l.text.strip() for l in a if l.text.strip()]
    if len(lt) != len(set(lt)): c.append(make_ch("Link Texts", "low", "warning", "Some duplicate link texts found."))
    else: c.append(make_ch("Link Texts", "medium", "pass", "Link texts are mostly unique."))

    return {"category": "Link Structure", "score": calc_score(c), "checks": c}

def chk_server(res, time_s, url):
    c = []
    # Status
    c.append(make_ch("HTTPS", "high", "pass" if url.startswith("https") else "fail", "HTTPS usage.", url))
    c.append(make_ch("Redirects", "high", "warning" if len(res.history) > 0 else "pass", f"Redirected {len(res.history)} time(s)."))
    
    h = {k.lower(): v for k, v in res.headers.items()}
    if "x-powered-by" in h: c.append(make_ch("HTTP Header", "high", "warning", "X-Powered-By exposed.", h["x-powered-by"]))
    else: c.append(make_ch("HTTP Header", "low", "pass", "No sensitive server headers exposed."))
    
    gzip = "content-encoding" in h and "gzip" in h["content-encoding"]
    c.append(make_ch("Compression", "high", "pass" if gzip else "warning", "Data compression (gzip) " + ("used." if gzip else "not detected.")))

    if time_s < 0.4: c.append(make_ch("Response Time", "low", "pass", f"Fast response ({time_s}s)."))
    elif time_s < 1.0: c.append(make_ch("Response Time", "medium", "warning", f"Moderate response ({time_s}s)."))
    else: c.append(make_ch("Response Time", "high", "fail", f"Slow response ({time_s}s)."))

    size = len(res.content) / 1024
    c.append(make_ch("Payload Size", "low", "pass" if size < 200 else "warning", f"{size:.1f} KB html size."))

    return {"category": "Server Config", "score": calc_score(c), "checks": c}

def analyze(url):
    if not url.startswith("http"): url = "http://" + url
    res, t_s = fetch_page(url)
    soup = BeautifulSoup(res.content, "html.parser")
    
    md = chk_meta(soup, url, res)
    cgs = {
        "meta_data": md,
        "page_quality": chk_quality(soup, md.get("title", "")),
        "headings": chk_others(soup),
        "link_structure": chk_links(soup, url),
        "server_configuration": chk_server(res, t_s, url)
    }
    
    t_sc = 0
    sum_d = {"passed": 0, "warnings": 0, "failed": 0, "total_checks": 0, "categories": {}}
    for k, d in cgs.items():
        t_sc += d["score"]
        c_sum = {"passed": 0, "warnings": 0, "failed": 0, "total_checks": 0}
        for ch in d["checks"]:
            st = ch["status"]
            sum_d["total_checks"] += 1
            c_sum["total_checks"] += 1
            if st == "pass": sum_d["passed"] += 1; c_sum["passed"] += 1
            elif st == "warning": sum_d["warnings"] += 1; c_sum["warnings"] += 1
            else: sum_d["failed"] += 1; c_sum["failed"] += 1
        sum_d["categories"][k] = c_sum

    return {
        "success": True,
        "target_url": url,
        "overall_seo_score": int(t_sc / len(cgs)),
        "summary": sum_d,
        "results": cgs
    }

@router.get("/seo-check")
def seo_check(url: str):
    return analyze(url)

@router.get("/seo-check/view", response_class=HTMLResponse)
def seo_check_html_view(url: str):
    data = analyze(url)
    t_url = data.get("target_url", url)
    summ = data.get("summary", {})
    res = data.get("results", {})
    osc = data.get("overall_seo_score", 0)
    
    sc_col = "text-danger" if osc < 50 else ("text-warning" if osc < 80 else "text-success")

    def b_col(s):
        if s == "pass": return "bg-success"
        if s == "warning": return "bg-warning text-dark"
        if s == "fail": return "bg-danger"
        return "bg-secondary"
        
    def p_col(p):
        if p == "critical": return "danger"
        if p == "high": return "warning text-dark"
        if p == "medium": return "primary"
        return "secondary"

    html = f"""
    <style>
        .score-circle {{ width: 110px; height: 110px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2.2rem; font-weight: bold; border: 8px solid; margin: 0 auto; }}
        .card {{ border-radius: 12px; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.03); }}
        .table th {{ background-color: #f8f9fa; font-size: 0.85rem; text-transform: uppercase; color: #6c757d; letter-spacing: 0.5px; }}
        .table-wrap {{ border-radius: 10px; overflow: hidden; border: 1px solid #e9ecef; margin-top: 15px; }}
        .accordion-button:not(.collapsed) {{ background-color: #e2e8f0; color: #1e293b; box-shadow: none; }}
    </style>
    <div class="container py-5">
        <div class="text-center mb-5">
            <h1 class="display-5 fw-bold mb-3 text-dark">SEO Analysis Report</h1>
            <a href="{t_url}" target="_blank" class="fs-5 text-decoration-none">{t_url}</a>
        </div>

        <div class="row g-4 mb-5 text-center justify-content-center">
            <div class="col-md-3">
                <div class="card h-100 p-4">
                    <div class="score-circle {sc_col}" style="border-color: currentColor;">{osc}</div>
                    <div class="mt-3 text-muted fw-semibold">OVERALL SCORE</div>
                </div>
            </div>
            <div class="col-md-9">
                <div class="row g-3 h-100">
                    <div class="col-md-3">
                        <div class="card border-top border-4 border-primary h-100"><div class="card-body py-4"><div class="text-muted fw-bold">TOTAL CHECKS</div><div class="fs-2 fw-bold text-primary">{summ.get("total_checks")}</div></div></div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-top border-4 border-success h-100"><div class="card-body py-4"><div class="text-muted fw-bold">PASSED</div><div class="fs-2 fw-bold text-success">{summ.get("passed")}</div></div></div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-top border-4 border-warning h-100"><div class="card-body py-4"><div class="text-muted fw-bold">WARNINGS</div><div class="fs-2 fw-bold text-warning">{summ.get("warnings")}</div></div></div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-top border-4 border-danger h-100"><div class="card-body py-4"><div class="text-muted fw-bold">FAILED</div><div class="fs-2 fw-bold text-danger">{summ.get("failed")}</div></div></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="accordion shadow-sm" id="seoAccordion" style="border-radius:12px;">
    """

    first = True
    for cat_slug, cat_data in res.items():
        c_title = cat_data.get("category", cat_slug.title())
        c_p = summ["categories"][cat_slug]["passed"]
        c_w = summ["categories"][cat_slug]["warnings"]
        c_f = summ["categories"][cat_slug]["failed"]
        sc = cat_data.get("score", 0)
        
        stat_b = f'<span class="badge bg-success ms-3">{c_p}</span><span class="badge bg-warning text-dark ms-1">{c_w}</span><span class="badge bg-danger ms-1">{c_f}</span>'
        sc_b = f'<span class="badge ms-auto {"bg-danger" if sc<50 else "bg-warning text-dark" if sc<80 else "bg-success"} fs-6 px-3 py-2">Score: {sc}</span>'
        
        html += f"""
            <div class="accordion-item border-0 border-bottom">
                <h2 class="accordion-header" id="h_{cat_slug}">
                    <button class="accordion-button {"" if first else "collapsed"} py-3 px-4" type="button" data-bs-toggle="collapse" data-bs-target="#c_{cat_slug}">
                        <strong class="fs-5">{c_title}</strong> {stat_b} {sc_b}
                    </button>
                </h2>
                <div id="c_{cat_slug}" class="accordion-collapse collapse {"show" if first else ""}" data-bs-parent="#seoAccordion">
                    <div class="accordion-body bg-white p-4">
                        <div class="table-responsive table-wrap">
                            <table class="table table-hover align-middle mb-0">
                                <thead>
                                    <tr>
                                        <th width="15%">Priority</th>
                                        <th width="20%">Check Name</th>
                                        <th width="10%">Status</th>
                                        <th width="35%">Details</th>
                                        <th width="20%">Found Value</th>
                                    </tr>
                                </thead>
                                <tbody>
        """
        for chk in cat_data.get("checks", []):
            val = f"<code>{chk['value'][:50]}...</code>" if chk['value'] and len(chk['value'])>50 else (f"<code>{chk['value']}</code>" if chk['value'] else '<span class="text-muted">-</span>')
            html += f"""
                                    <tr>
                                        <td><span class="badge bg-{p_col(chk['priority'])} w-100 py-2">{chk['priority'].upper()}</span></td>
                                        <td class="fw-bold">{chk['name']}</td>
                                        <td><span class="badge {b_col(chk['status'])} w-100 py-2 text-uppercase">{chk['status']}</span></td>
                                        <td class="text-secondary">{chk['message']}</td>
                                        <td>{val}</td>
                                    </tr>
            """
        html += """
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        """
        first = False

    html += """
        </div>
    </div>
    """
    return html

