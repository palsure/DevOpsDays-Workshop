#!/usr/bin/env python3
"""
generate_pptx.py
Generates a PowerPoint presentation for the DevOpsDays QoE Workshop.
Run from the presentations/ directory:
    python3 generate_pptx.py

Output: DevOpsDays-QoE-Workshop.pptx
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ─── Theme colours ──────────────────────────────────────────────────────────
C_BG        = RGBColor(0x0F, 0x17, 0x23)   # near-black background
C_SURFACE   = RGBColor(0x1A, 0x24, 0x34)   # card / surface
C_ACCENT    = RGBColor(0x38, 0xBD, 0xF8)   # sky-blue accent
C_TEXT      = RGBColor(0xE2, 0xE8, 0xF0)   # primary text
C_SECONDARY = RGBColor(0x94, 0xA3, 0xB8)   # muted text
C_SUCCESS   = RGBColor(0x34, 0xD3, 0x99)   # green
C_WARNING   = RGBColor(0xFB, 0xBF, 0x24)   # amber
C_DANGER    = RGBColor(0xF8, 0x71, 0x71)   # red
C_WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
C_HEADER_BG = RGBColor(0x1E, 0x40, 0xAF)   # indigo for table headers

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def new_prs():
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs

def blank_slide(prs):
    layout = prs.slide_layouts[6]  # blank
    slide  = prs.slides.add_slide(layout)
    # dark background
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = C_BG
    return slide

def add_rect(slide, x, y, w, h, fill_color=None, line_color=None):
    shape = slide.shapes.add_shape(1, x, y, w, h)  # MSO_SHAPE_TYPE.RECTANGLE
    shape.line.fill.background() if line_color is None else None
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(0.5)
    return shape

def add_textbox(slide, text, x, y, w, h,
                size=18, bold=False, color=None, align=PP_ALIGN.LEFT,
                wrap=True, italic=False):
    txb = slide.shapes.add_textbox(x, y, w, h)
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    run.font.color.rgb = color if color else C_TEXT
    return txb

def add_label(slide, text, x, y, w=Inches(12), size=11,
              color=None, bold=False, italic=False):
    add_textbox(slide, text, x, y, w, Inches(0.35),
                size=size, color=color or C_SECONDARY,
                bold=bold, italic=italic)

def section_divider(slide, section_text):
    """Left accent bar + section label."""
    add_rect(slide, Inches(0.4), Inches(0.15), Inches(0.06), Inches(0.35), C_ACCENT)
    add_label(slide, section_text.upper(), Inches(0.55), Inches(0.13),
              size=9, color=C_ACCENT, bold=True)

def slide_title(slide, title, subtitle=None):
    section_divider(slide, "")
    add_textbox(slide, title,
                Inches(0.5), Inches(0.5), Inches(12.3), Inches(0.7),
                size=28, bold=True, color=C_WHITE)
    if subtitle:
        add_textbox(slide, subtitle,
                    Inches(0.5), Inches(1.1), Inches(12.3), Inches(0.4),
                    size=14, color=C_SECONDARY)

def h2(slide, text, x, y, w=Inches(12)):
    add_textbox(slide, text, x, y, w, Inches(0.45), size=16, bold=True, color=C_ACCENT)

def h3(slide, text, x, y, w=Inches(5.8)):
    add_textbox(slide, text, x, y, w, Inches(0.35), size=13, bold=True, color=C_TEXT)

def bullet(slide, items, x, y, w=Inches(5.8), size=11, color=None):
    """Render a list of strings as bullet points in a single textbox."""
    txb = slide.shapes.add_textbox(x, y, w, Inches(0.3 * len(items) + 0.1))
    tf  = txb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"  \u2022  {item}"
        p.font.size  = Pt(size)
        p.font.color.rgb = color if color else C_TEXT

def code_box(slide, code_text, x, y, w, h, size=9):
    rect = add_rect(slide, x, y, w, h, fill_color=C_SURFACE, line_color=RGBColor(0x33, 0x44, 0x55))
    txb  = slide.shapes.add_textbox(x + Inches(0.1), y + Inches(0.05),
                                    w - Inches(0.2), h - Inches(0.1))
    tf   = txb.text_frame
    tf.word_wrap = False
    p    = tf.paragraphs[0]
    run  = p.add_run()
    run.text = code_text.strip()
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(0x7D, 0xD3, 0xFC)   # light-blue mono

def simple_table(slide, headers, rows, x, y, w, col_widths=None, font_size=9):
    """Draw a table manually using rectangles and text."""
    n_cols = len(headers)
    if col_widths is None:
        col_w = w / n_cols
        col_widths = [col_w] * n_cols

    row_h = Inches(0.28)
    # Header row
    cx = x
    for ci, hdr in enumerate(headers):
        cw = col_widths[ci]
        add_rect(slide, cx, y, cw, row_h, fill_color=C_HEADER_BG)
        add_textbox(slide, hdr, cx + Inches(0.05), y + Inches(0.04),
                    cw - Inches(0.08), row_h - Inches(0.06),
                    size=font_size, bold=True, color=C_WHITE)
        cx += cw

    # Data rows
    for ri, row in enumerate(rows):
        ry = y + row_h * (ri + 1)
        bg = C_SURFACE if ri % 2 == 0 else RGBColor(0x0F, 0x1E, 0x2E)
        cx = x
        for ci, cell in enumerate(row):
            cw = col_widths[ci]
            add_rect(slide, cx, ry, cw, row_h, fill_color=bg,
                     line_color=RGBColor(0x1E, 0x30, 0x40))
            text = str(cell)
            add_textbox(slide, text, cx + Inches(0.05), ry + Inches(0.04),
                        cw - Inches(0.08), row_h - Inches(0.06),
                        size=font_size, color=C_TEXT)
            cx += cw

def callout_box(slide, title, body, x, y, w, h, tone="info"):
    colors = {"info": C_ACCENT, "warning": C_WARNING, "danger": C_DANGER, "success": C_SUCCESS}
    bar_color = colors.get(tone, C_ACCENT)
    add_rect(slide, x, y, w, h, fill_color=C_SURFACE)
    add_rect(slide, x, y, Inches(0.05), h, fill_color=bar_color)
    add_textbox(slide, title, x + Inches(0.12), y + Inches(0.05),
                w - Inches(0.15), Inches(0.25), size=10, bold=True, color=C_WHITE)
    add_textbox(slide, body, x + Inches(0.12), y + Inches(0.28),
                w - Inches(0.15), h - Inches(0.35), size=9, color=C_SECONDARY)

def stat_box(slide, value, label, x, y, w=Inches(2.8), tone=None):
    color_map = {"success": C_SUCCESS, "warning": C_WARNING, "danger": C_DANGER}
    val_color = color_map.get(tone, C_ACCENT)
    add_rect(slide, x, y, w, Inches(0.85), fill_color=C_SURFACE)
    add_textbox(slide, value, x, y + Inches(0.05), w, Inches(0.42),
                size=26, bold=True, color=val_color, align=PP_ALIGN.CENTER)
    add_textbox(slide, label, x, y + Inches(0.47), w, Inches(0.35),
                size=9, color=C_SECONDARY, align=PP_ALIGN.CENTER)

def slide_number(slide, n, total):
    add_textbox(slide, f"{n} / {total}",
                Inches(12.1), Inches(7.1), Inches(1.1), Inches(0.3),
                size=8, color=RGBColor(0x44, 0x55, 0x66), align=PP_ALIGN.RIGHT)

# ─── Slide builders ──────────────────────────────────────────────────────────

def build_title_slide(prs):
    slide = blank_slide(prs)
    # Accent bar left
    add_rect(slide, Inches(0), Inches(0), Inches(0.1), SLIDE_H, fill_color=C_ACCENT)
    # Tag line
    add_textbox(slide, "DEVOPSDAYS RALEIGH 2026",
                Inches(0.5), Inches(1.8), Inches(12), Inches(0.4),
                size=11, color=C_ACCENT, bold=True,
                align=PP_ALIGN.CENTER)
    add_textbox(slide, "Cross-Platform Streaming QoE Validation\nin CI/CD Pipelines",
                Inches(0.5), Inches(2.3), Inches(12), Inches(1.4),
                size=36, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_textbox(slide,
                "How to detect quality regressions before they reach your viewers\n"
                "— across web, iOS, Android, and beyond.",
                Inches(1.5), Inches(3.8), Inches(10), Inches(0.8),
                size=14, color=C_SECONDARY, align=PP_ALIGN.CENTER)
    # Stats row
    for i, (v, l) in enumerate([
        ("3–4 hrs", "Workshop Duration"),
        ("Advanced", "Level"),
        ("Hands-on Lab", "Format"),
    ]):
        stat_box(slide, v, l, Inches(1.5 + i * 3.2), Inches(5.2), Inches(3.0))
    return slide


def build_agenda(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Agenda")
    rows = [
        ("1", "Streaming Platforms — web, mobile, smart TV, console", "20 min"),
        ("2", "How quality issues affect users and revenue", "15 min"),
        ("3", "Testing taxonomy — unit, acceptance, smoke, regression", "25 min"),
        ("4", "CI/CD advantages — why automate quality gates", "15 min"),
        ("5", "Pipeline architecture — path filters, stages, fallbacks", "30 min"),
        ("6", "Slack bot setup — notifications and threaded reports", "15 min"),
        ("7", "Firebase setup — distribution and crash monitoring", "15 min"),
        ("8", "GitHub Actions — setup, builds, release process", "20 min"),
        ("9", "Hands-on labs", "60 min"),
    ]
    simple_table(slide, ["#", "Topic", "Duration"], rows,
                 Inches(0.5), Inches(1.4), Inches(12.3),
                 col_widths=[Inches(0.4), Inches(10.3), Inches(1.6)])
    return slide


def build_qoe_overview(prs):
    slide = blank_slide(prs)
    slide_title(slide, "What is QoE?", "Quality of Experience vs Quality of Service")
    h2(slide, "Key QoE Metrics", Inches(0.5), Inches(1.4))
    metrics = [
        ("Startup Time",       "Time from Play to first frame. Target < 2 s"),
        ("Rebuffering Ratio",  "% of watch time spent buffering. Target < 0.5%"),
        ("Bitrate Switches",   "ABR ladder changes per minute. Fewer = smoother"),
        ("Error Rate",         "Fatal + non-fatal playback errors per session"),
        ("Playback Quality",   "Composite score: excellent / good / fair / poor"),
        ("Join Rate",          "% of play attempts that successfully start"),
    ]
    simple_table(slide, ["Metric", "Description"], metrics,
                 Inches(0.5), Inches(1.85), Inches(12.3),
                 col_widths=[Inches(2.5), Inches(9.8)])
    callout_box(slide, "QoS vs QoE",
                "A stream can have perfect QoS (no packet loss, great bandwidth) "
                "and still give a poor QoE (high startup time, frequent quality switches). "
                "QoE is measured at the player, not the network.",
                Inches(0.5), Inches(5.4), Inches(12.3), Inches(0.9), "info")
    return slide


# ── SECTION: Platforms ───────────────────────────────────────────────────────

def build_platforms_overview(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Streaming Platforms Landscape")
    rows = [
        ("Web Browser",     "Chrome, Safari, Firefox, Edge",                       "~40% of sessions"),
        ("Mobile — iOS",    "iPhone, iPad — AVPlayer / HLS native",                "~25% of sessions"),
        ("Mobile — Android","ExoPlayer, MediaPlayer — diverse hardware",            "~20% of sessions"),
        ("Smart TV",        "Roku, Samsung Tizen, LG webOS, Android TV",           "~10% and growing"),
        ("Streaming Sticks","Fire TV, Chromecast, Apple TV",                       "~3%"),
        ("Gaming Console",  "PlayStation, Xbox",                                   "~2%"),
    ]
    simple_table(slide, ["Category", "Platforms", "Market Reach"], rows,
                 Inches(0.5), Inches(1.4), Inches(12.3),
                 col_widths=[Inches(2.2), Inches(7.1), Inches(3.0)])
    callout_box(slide, "Fragmentation Challenge",
                "A single streaming service may target 15+ device classes — each with different codec "
                "support (H.264, H.265, AV1), DRM (Widevine, FairPlay, PlayReady), ABR behaviour, "
                "and memory constraints.",
                Inches(0.5), Inches(5.4), Inches(12.3), Inches(0.9), "warning")
    return slide


def build_platform_stacks(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Platform Tech Stacks & Testing Tools")
    simple_table(slide, ["Platform", "Player", "DRM", "Unit Tests", "E2E Tests", "CI Runner"],
        [
            ("Web",        "HLS.js / Shaka Player", "Widevine / FairPlay",    "Vitest",       "Playwright",       "ubuntu-latest"),
            ("iOS",        "AVPlayer",              "FairPlay (FPS)",         "XCTest",        "XCUITest",         "macos-latest"),
            ("Android",    "ExoPlayer (Media3)",    "Widevine L1/L3",         "JUnit 5",      "Espresso",         "ubuntu-latest"),
            ("Samsung TV", "Shaka / AVPlay",        "PlayReady",              "Jest",         "Selenium/Tizen",   "ubuntu-latest"),
            ("Roku",       "Native Media Player",   "PlayReady / Widevine",   "BrightScript", "Roku sideload",    "ubuntu-latest"),
            ("Apple TV",   "AVPlayer",              "FairPlay",               "XCTest",       "XCUITest",         "macos-latest"),
            ("Fire TV",    "ExoPlayer",             "Widevine",               "JUnit 5",      "ADB + Espresso",   "ubuntu-latest"),
        ],
        Inches(0.5), Inches(1.4), Inches(12.3),
        col_widths=[Inches(1.4), Inches(2.0), Inches(2.1), Inches(1.6), Inches(1.8), Inches(3.4)],
        font_size=9)
    return slide


def build_video_delivery(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Video Delivery Architecture")
    code_box(slide, """
Origin (FFmpeg/Packager)          CDN Edge (Nginx :8081)          Player
  HLS multi-bitrate renditions  ──►  Cache-Control, CORS,     ──►  ABR Engine
    360p  800 kbps                    Range headers                 Manifest request
    720p  2.5 Mbps                                                  Segment requests
    1080p 5 Mbps                                                    Bitrate selection
    4K    15 Mbps                                                   QoE Metrics SDK
                                                                         │
                                                              POST /api/v1/metrics
                                                                         │
                                                              Backend API (Spring Boot)
                                                              PostgreSQL metrics store
""",
    Inches(0.4), Inches(1.4), Inches(12.5), Inches(3.8))
    callout_box(slide, "Local CI Stack",
                "In this workshop, Nginx on port 8081 simulates the CDN edge. HLS segments "
                "and manifests are served with proper Range and CORS headers.",
                Inches(0.4), Inches(5.4), Inches(12.5), Inches(0.9), "info")
    return slide


# ── SECTION: Quality Impact ──────────────────────────────────────────────────

def build_quality_impact(prs):
    slide = blank_slide(prs)
    slide_title(slide, "How Quality Issues Affect Viewers")
    for i, (v, l, t) in enumerate([
        ("47%",   "viewers abandon after 20 s of buffering",              "danger"),
        ("3x",    "higher churn for users with startup > 4 s",            "danger"),
        ("$2.16B","estimated annual revenue lost to streaming QoE issues", "warning"),
    ]):
        stat_box(slide, v, l, Inches(0.5 + i * 4.2), Inches(1.4), Inches(3.9), t)
    rows = [
        ("Startup > 3 s",         "\"App is broken\" — viewer switches away",     "Drop in session starts, negative reviews"),
        ("Rebuffering > 1%",      "Frustration, loses track of content",           "15–30% increase in abandonment"),
        ("Bitrate downgrade",     "Blurry picture — \"bad service\"",              "Subscription cancellations in premium tiers"),
        ("Audio/video sync",      "Jarring, unwatchable",                          "Immediate exit, social media complaints"),
        ("DRM errors",            "\"Can't play this video\" — no recovery",       "Support tickets, refund requests"),
        ("Crash on launch",       "No experience at all",                          "1-star reviews, app store ranking drop"),
    ]
    simple_table(slide, ["Issue", "User Perception", "Business Impact"], rows,
                 Inches(0.5), Inches(2.5), Inches(12.3),
                 col_widths=[Inches(2.3), Inches(4.5), Inches(5.5)])
    return slide


def build_qoe_scoring(prs):
    slide = blank_slide(prs)
    slide_title(slide, "QoE Scoring Model — Release Gate Thresholds")
    code_box(slide, """
// ValidationEngine.java — composite scoring
double score = 1.0;

if (startupTime > 3000)          score -= 0.25;   // 25% penalty  (threshold: 3 s)
if (totalBufferingTime > 5)      score -= 0.30;   // 30% penalty  (threshold: 5 s cumulative)
if (errorCount > 2)              score -= 0.25;   // 25% penalty  (threshold: 2 errors)
if (bitrateSwitches > 10)        score -= 0.10;   // 10% penalty  (threshold: 10 switches)
if (currentBitrate < 500_000)    score -= 0.10;   // 10% penalty  (threshold: 500 kbps)

String quality = score >= 0.9 ? "excellent"   // all metrics nominal
               : score >= 0.7 ? "good"        // one minor issue
               : score >= 0.5 ? "fair"        // notable degradation
               : "poor";                      // gate FAILS
""",
    Inches(0.5), Inches(1.45), Inches(12.3), Inches(3.3))
    for i, (val, lbl, tone) in enumerate([
        (">= 0.9", "excellent", "success"),
        (">= 0.7", "good",      "success"),
        (">= 0.5", "fair",      "warning"),
        ("< 0.5",  "poor — gate fails", "danger"),
    ]):
        stat_box(slide, val, lbl, Inches(0.5 + i * 3.1), Inches(5.0), Inches(2.9), tone)
    return slide


# ── SECTION: Test Types ──────────────────────────────────────────────────────

def build_test_pyramid(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Testing Pyramid for Streaming QoE")
    code_box(slide, """
                        ╔══════════════════╗
                       ╔╝   Acceptance      ╚╗   < 30 min · cross-platform 80% gate
                      ╔══════════════════════╗
                     ╔╝  E2E / Playwright     ╚╗  ~10 min per module · full Docker stack
                    ╔══════════════════════════╗
                   ╔╝  Integration / REST Assured╚╗  ~5 min · Testcontainers
                  ╔══════════════════════════════╗
                 ╔╝          Unit Tests           ╚╗  < 2 min · all modules
                ╚══════════════════════════════════╝

    SLOWER / FEWER / MORE DEPS ↑          ↑ HIGHER CONFIDENCE PER TEST
    FASTER / MORE / ISOLATED   ↓          ↓ LOWER COST TO WRITE & MAINTAIN
""",
    Inches(0.5), Inches(1.45), Inches(12.3), Inches(4.2))
    callout_box(slide, "Keep the pyramid shape",
                "Aim for ~60% unit, ~30% integration+E2E, ~10% acceptance. "
                "An inverted pyramid (mostly E2E) is slow, fragile, and expensive to maintain.",
                Inches(0.5), Inches(5.8), Inches(12.3), Inches(0.6), "warning")
    return slide


def build_test_types(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Testing Taxonomy — All Types")
    rows = [
        ("Unit",           "JUnit 5 / Vitest / XCTest",    "< 2 min",      "No external deps",    "Validation rules, scoring, parsers"),
        ("Integration",    "Spring Test + Testcontainers",  "1–5 min",      "Docker — DB only",    "API ↔ Postgres, REST contracts"),
        ("E2E / Functional","Playwright / REST Assured",    "5–15 min",     "Full Docker stack",   "Playback flow, metric POST"),
        ("Smoke",          "curl / custom script",          "< 2 min",      "Deployed environment","Health, metric POST 201, player loads"),
        ("Regression",     "@Tag(\"regression\") tests",   "5–20 min",     "CI / staging",        "Previously-fixed bugs stay fixed"),
        ("Acceptance",     "Maven/TestNG matrix",           "15–30 min",    "Docker + CI matrix",  "80% gate before release"),
        ("Performance",    "k6 / Gatling / Lighthouse",    "Varies",       "Load generator",      "Startup time under 1,000 concurrent"),
        ("Compatibility",  "Playwright matrix projects",   "10–20 min",    "Browser matrix",      "Same test, multiple browsers/OS"),
        ("Network Sim",    "Playwright throttle / tc-netem","5–10 min",    "tc or Playwright",    "3G throttle, CDN delay, packet loss"),
    ]
    simple_table(slide, ["Type", "Tool", "Speed", "Environment", "Catches"],
                 rows, Inches(0.5), Inches(1.4), Inches(12.3),
                 col_widths=[Inches(1.7), Inches(2.6), Inches(1.3), Inches(2.1), Inches(4.6)],
                 font_size=9)
    return slide


def build_acceptance_tests(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Build Acceptance Tests — Release Gate")
    h2(slide, "Gate Flow", Inches(0.5), Inches(1.4))
    code_box(slide, """
[Unit Tests] → [E2E Tests] → POST /api/v1/pipeline-runs (create run)
                                  │  push per-platform counts (api, web, android, ios, automation)
                                  │  POST /api/v1/pipeline-runs/{id}/finalize
                                  │
                             passed >= 80%?
                        ┌──────────┴──────────┐
                       YES                    NO
                        │                     │
                  status=RELEASED       status=BLOCKED
                  → GitHub Release      → Block merge
                  → Slack success       → Slack failure
""",
    Inches(0.5), Inches(1.85), Inches(12.3), Inches(3.0))
    simple_table(slide, ["Pass Rate", "Status", "Action"],
        [
            (">= 80%",  "RELEASED", "Create GitHub Release, Slack success"),
            ("< 80%",   "BLOCKED",  "Block merge, Slack alert"),
            ("No data", "PENDING",  "Workflow fails — no results submitted"),
        ],
        Inches(0.5), Inches(5.1), Inches(12.3),
        col_widths=[Inches(2.0), Inches(2.0), Inches(8.3)])
    return slide


def build_smoke_tests(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Smoke Tests — First Check After Deploy")
    h2(slide, "Smoke Test Checklist", Inches(0.5), Inches(1.4))
    simple_table(slide, ["Check", "Pass Criterion"],
        [
            ("API health",           "/actuator/health → {status: UP}"),
            ("DB connectivity",      "GET /api/v1/metrics returns 200 (not 503)"),
            ("Web player loads",     "React SPA renders, no console errors"),
            ("Nginx serving content","GET /videos/ returns 200"),
            ("Metric POST accepted", "POST /api/v1/metrics → 201"),
            ("Pipeline API up",      "GET /api/v1/pipeline-runs/latest → 200"),
        ],
        Inches(0.5), Inches(1.85), Inches(8.0),
        col_widths=[Inches(2.8), Inches(5.2)])
    code_box(slide, """#!/bin/bash
BASE="${API_BASE:-http://localhost:8080}"
curl -sf "$BASE/actuator/health" | grep '"UP"'
curl -sf -X POST "$BASE/api/v1/metrics" \\
  -H "Content-Type: application/json" \\
  -d '{"platform":"smoke","sessionId":"sm-1",
       "timestamp":"2026-01-01T00:00:00Z",
       "videoId":"smoke","metrics":{"startupTime":100}}' \\
  | grep '"id"'
echo "All smoke tests passed"
""",
    Inches(8.6), Inches(1.4), Inches(4.6), Inches(3.5), size=8)
    return slide


def build_regression_tests(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Regression Tests — Bugs That Must Stay Fixed")
    h2(slide, "Tag & Track Every Production Bug", Inches(0.5), Inches(1.4))
    code_box(slide, """@Test
@Tag("regression")
@Tag("bug-QOE-412")
void platformNormalization_appletv_caseSensitive() {
    // Bug: "APPLE_TV" was rejected; correct normalised key is "APPLETV"
    String normalised = Platform.normalize("APPLE_TV");
    assertEquals("APPLETV", normalised);
}""",
    Inches(0.5), Inches(1.85), Inches(6.0), Inches(2.2))
    simple_table(slide, ["Bug Type", "Test Home"],
        [
            ("Validation logic regression",    "Unit — ValidationEngineTest"),
            ("API schema break",               "Integration — REST Assured"),
            ("Platform-specific metric miss",  "E2E — Playwright / XCUITest"),
            ("Quality score drift",            "Unit — scoring formula tests"),
            ("DRM error not caught",           "Integration — mock license server"),
            ("Pipeline run not finalised",     "Integration — PipelineRunServiceTest"),
        ],
        Inches(6.8), Inches(1.85), Inches(6.0),
        col_widths=[Inches(3.2), Inches(2.8)])
    callout_box(slide, "Run only regression tests",
                "./gradlew test -Ptags=regression",
                Inches(0.5), Inches(4.3), Inches(6.0), Inches(0.65), "info")
    return slide


# ── SECTION: CI/CD Benefits ──────────────────────────────────────────────────

def build_cicd_benefits(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Why Run Tests in CI/CD Pipelines?")
    for i, (v, l, t) in enumerate([
        ("10x",     "cheaper to fix a bug in CI vs production", "success"),
        ("< 15 min","time-to-feedback per module commit",        "success"),
        ("0",       "manual test runs needed on merge",          "success"),
    ]):
        stat_box(slide, v, l, Inches(0.5 + i * 4.1), Inches(1.4), Inches(3.8), t)
    rows = [
        ("Shift-left testing",   "Bugs found at commit time, not post-release — 10x cheaper to fix"),
        ("Consistent environment","Same Docker stack every run — no 'works on my machine'"),
        ("Parallel execution",   "Multi-platform matrix runs simultaneously — no waiting"),
        ("Audit trail",          "Every test result tied to commit SHA and build number"),
        ("Release confidence",   "Quality gate blocks bad builds before they reach production"),
        ("Fast feedback",        "Threaded Slack notifications — know status within minutes per stage"),
        ("Path filtering",       "Only the affected module's pipeline runs — saves 70% runner minutes"),
    ]
    simple_table(slide, ["Benefit", "Detail"], rows,
                 Inches(0.5), Inches(2.5), Inches(12.3),
                 col_widths=[Inches(2.5), Inches(9.8)])
    return slide


def build_path_filtering(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Module-Isolated Pipelines — Path Filtering")
    code_box(slide, """# qoe-api-tests.yml
on:
  push:
    paths:
      - 'backend-api/**'             # API source code
      - 'qoe-automation-tests/**'    # Shared automation suite
      - 'docker-compose.yml'         # Compose stack
      - '.github/workflows/qoe-api-tests.yml'   # Self-trigger on workflow changes
      - '.github/scripts/api_tests_to_slack.py' # Script changes also trigger
  pull_request:
    paths:
      - 'backend-api/**'
      - '.github/workflows/qoe-api-tests.yml'""",
    Inches(0.5), Inches(1.4), Inches(12.3), Inches(3.2))
    simple_table(slide, ["Workflow", "Triggered When These Paths Change"],
        [
            ("qoe-api-tests.yml",     "backend-api/** | docker-compose.yml | qoe-automation-tests/**"),
            ("qoe-web-tests.yml",     "web-player/** | docker-compose.yml | qoe-automation-tests/**"),
            ("qoe-android-tests.yml", "android-player/** | qoe-automation-tests/**"),
            ("qoe-ios-tests.yml",     "ios-player/** | qoe-automation-tests/**"),
            ("qoe-validation.yml",    "any module (PR only — lightweight compile + unit)"),
            ("qoe-pr-e2e.yml",        "backend-api/**, web-player/**, docker-compose.yml (PR only)"),
        ],
        Inches(0.5), Inches(4.85), Inches(12.3),
        col_widths=[Inches(2.8), Inches(9.5)])
    return slide


# ── SECTION: Pipeline Architecture ──────────────────────────────────────────

def build_arch_overview(prs):
    slide = blank_slide(prs)
    slide_title(slide, "CI/CD Pipeline Architecture — Overview")
    code_box(slide, """
Developer Push / PR
  │
  ├─ Push to backend-api/**  ──────────────► qoe-api-tests.yml
  │                                            Stage 1: Unit Tests (Gradle)
  │                                            Stage 2: E2E Matrix (3 platforms)
  │                                            Stage 3: Automation E2E (Maven/TestNG)
  │                                            Stage 4: Allure Report + Slack Summary
  │
  ├─ Push to web-player/**   ──────────────► qoe-web-tests.yml
  │                                            Stage 1: Unit + Lint (Vitest)
  │                                            Stage 2: Playwright E2E
  │                                            Stage 3: Automation E2E
  │                                            Stage 4: Report + Slack
  │
  ├─ Push to android-player/**  ───────────► qoe-android-tests.yml
  │                                            Stage 1: Unit + Lint (Gradle)
  │                                            Stage 2: Build APK
  │                                            Stage 3: Automation E2E
  │                                            Stage 4: Report + Slack
  │
  ├─ Push to ios-player/**   ──────────────► qoe-ios-tests.yml
  │                                            Stage 1: swift test
  │                                            Stage 2: Xcode Build (Simulator)
  │                                            Stage 3: Automation E2E
  │                                            Stage 4: Report + Slack
  │
  └─ Pull Request  ─────────────────────────► qoe-validation.yml (lightweight)
                                            ► qoe-pr-e2e.yml (full E2E gate)

Manual trigger  ─────────────────────────────► build-acceptance-release.yml
                                                Cross-module acceptance + Release
""",
    Inches(0.4), Inches(1.4), Inches(12.5), Inches(5.9), size=8)
    return slide


def build_quality_gate(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Quality Gate — Design & Configuration")
    code_box(slide, """
# 1. Create run
RUN=$(curl -sS -X POST "$API/api/v1/pipeline-runs"
  -d '{"githubRunId":"${{ github.run_id }}"}' | jq -r .runId)

# 2. Push per-platform results (once per module acceptance job)
for platform in api web android ios automation; do
  curl -X POST "$API/api/v1/pipeline-runs/$RUN/platforms"
    -d '{"platform":"'$platform'","passed":'$P',"failed":'$F',"total":'$T'}'
done

# 3. Finalize — compute aggregate pass rate
curl -X POST "$API/api/v1/pipeline-runs/$RUN/finalize"
# Response: { "status": "RELEASED", "passRate": 0.94 }
""",
    Inches(0.5), Inches(1.45), Inches(7.5), Inches(3.3))
    simple_table(slide, ["Pass Rate", "Status", "Action"],
        [
            (">= 80%",  "RELEASED", "Create GitHub Release, Slack success"),
            ("< 80%",   "BLOCKED",  "Block deploy, Slack failure"),
            ("No data", "PENDING",  "Workflow fails — no results submitted"),
        ],
        Inches(8.2), Inches(1.45), Inches(4.6),
        col_widths=[Inches(1.2), Inches(1.3), Inches(2.1)])
    callout_box(slide, "Fallback: continue-on-error",
                "E2E matrix jobs use continue-on-error: true so one flaky platform "
                "runner does not block the others from reporting. The report job collects "
                "all results regardless.",
                Inches(0.5), Inches(5.0), Inches(7.5), Inches(0.9), "warning")
    callout_box(slide, "Configurable threshold",
                "QUALITY_GATE_THRESHOLD=80 in application.yml. "
                "Raise to 95% for production, lower for experimental branches.",
                Inches(8.2), Inches(3.0), Inches(4.6), Inches(1.0), "info")
    return slide


def build_fallback_options(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Fallback Options in the Pipeline")
    rows = [
        ("E2E fails on one platform",  "continue-on-error: true",          "e2e-tests matrix job"),
        ("Docker compose start fails", "if: always() on upload/report",    "All E2E jobs"),
        ("Allure report gen fails",    "Placeholder index.html created",   "api-report job"),
        ("Slack token missing",        "if: env.SLACK_BOT_TOKEN != '' guard","All Slack steps"),
        ("GitHub Pages not enabled",  "Fallback to Actions artifact URL",  "api_tests_to_slack.py"),
        ("Quality gate API down",      "Workflow fails → retry via dispatch","build-acceptance-release.yml"),
        ("iOS build fails",            "set -o pipefail — no silent || true","qoe-ios-tests.yml"),
        ("Runner OOM / hung",          "timeout-minutes: 30 kills the job", "All long-running jobs"),
    ]
    simple_table(slide, ["Failure Scenario", "Fallback Mechanism", "Configured In"],
                 rows, Inches(0.5), Inches(1.4), Inches(12.3),
                 col_widths=[Inches(3.3), Inches(4.2), Inches(4.8)])
    callout_box(slide, "Manual escape hatch",
                "build-acceptance-release.yml is workflow_dispatch only. A release manager "
                "can trigger it at any time, choose the ref, and decide whether to create a "
                "GitHub Release — preventing accidental production releases.",
                Inches(0.5), Inches(5.5), Inches(12.3), Inches(0.85), "info")
    return slide


def build_slack_arch(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Slack Notifications — Threaded Architecture")
    code_box(slide, """
notify-start job                              Slack channel
  │                                             ┌─────────────────────────────────────┐
  │  curl chat.postMessage                      │ [API] Build Started | Build #42     │
  └─► save thread_ts as artifact                │ Branch: main  Commit: abc1234        │
                                                └─────────────────────────────────────┘
unit-tests job (needs: notify-start)                    │
  │                                                     ▼ thread reply
  │  python3 stage_result_to_slack.py           ┌─────────────────────────────────────┐
  └─► reads THREAD_TS, posts reply              │ ✓ Unit Tests PASSED | Build #42     │
                                                │ Passed: 47  Failed: 0  Rate: 100%   │
e2e-tests job                                   └─────────────────────────────────────┘
  │                                                     │
  │  python3 stage_result_to_slack.py                   ▼ thread reply
  └─► reads THREAD_TS, posts reply              ┌─────────────────────────────────────┐
                                                │ ✓ E2E Tests PASSED | Build #42      │
api-report job (if: always())                   │ Passed: 18  Failed: 0  Rate: 90%    │
  │                                             │ Report: <link|Allure>               │
  │  python3 module_result_to_slack.py          └─────────────────────────────────────┘
  └─► overall summary message (top-level)              │
                                                       ▼ top-level summary
                                               ┌─────────────────────────────────────┐
                                               │ [API] Build PASSED | 18 min         │
                                               │ Unit ✓ | E2E ✓ | Automation ✓       │
                                               └─────────────────────────────────────┘
""",
    Inches(0.4), Inches(1.4), Inches(12.5), Inches(5.3), size=8)
    return slide


# ── SECTION: Slack Bot Setup ─────────────────────────────────────────────────

def build_slack_setup(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Slack Bot — Create App & Get Token")
    simple_table(slide, ["Step", "Location", "Action"],
        [
            ("1", "api.slack.com/apps",             "Create New App → From scratch"),
            ("2", "App Name",                       "QoE CI Bot"),
            ("3", "Workspace",                      "Select your workspace → Create App"),
            ("4", "OAuth & Permissions → Scopes",   "Add: chat:write, chat:write.public"),
            ("5", "OAuth & Permissions",             "Install to Workspace → Allow"),
            ("6", "OAuth Tokens section",            "Copy Bot User OAuth Token (xoxb-...)"),
            ("7", "Slack channel",                   "/invite @QoE CI Bot  (must be invited)"),
            ("8", "GitHub repo → Settings → Secrets","Add SLACK_BOT_TOKEN and SLACK_CHANNEL_ID"),
        ],
        Inches(0.5), Inches(1.45), Inches(12.3),
        col_widths=[Inches(0.4), Inches(3.5), Inches(8.4)])
    callout_box(slide, "Finding Channel ID",
                "Open the channel in Slack → right-click name → View channel details → "
                "Copy the ID at the bottom (starts with C for public, G for private). "
                "Or read the URL: last segment after /archives/",
                Inches(0.5), Inches(5.5), Inches(12.3), Inches(0.9), "info")
    return slide


def build_slack_blockkit(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Slack Block Kit — Message Format")
    code_box(slide, """{
  "channel": "C0XXXXXXXXX",
  "unfurl_links": false,
  "unfurl_media": false,
  "blocks": [
    { "type": "header",
      "text": { "type": "plain_text",
                "text": "[API] Build Started | Build #42" } },
    { "type": "section",
      "text": { "type": "mrkdwn",
                "text": "*Branch:* main  *Commit:* <https://github.com/.../commit/abc|abc1234>" } },
    { "type": "divider" },
    { "type": "section",
      "text": { "type": "mrkdwn",
                "text": ":white_check_mark: *Unit Tests* PASSED — 47/47 · 100%" } }
  ]
}""",
    Inches(0.5), Inches(1.45), Inches(6.0), Inches(4.2))
    simple_table(slide, ["mrkdwn Element", "Syntax"],
        [
            ("Bold",          "*text*"),
            ("Clickable link","<url|label>"),
            ("Emoji",         ":white_check_mark:  :red_circle:"),
            ("Thread reply",  "Set thread_ts field in payload"),
            ("No link cards", "unfurl_links: false"),
            ("No code block", "Remove triple backtick — needed for emoji to render"),
        ],
        Inches(6.8), Inches(1.45), Inches(6.0),
        col_widths=[Inches(2.2), Inches(3.8)])
    return slide


# ── SECTION: Firebase Setup ──────────────────────────────────────────────────

def build_firebase_overview(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Firebase — Platform Services for Mobile CI")
    rows = [
        ("App Distribution",    "Distribute test builds to testers without App Store / Play Store"),
        ("Test Lab",            "Run instrumented Android tests on real Google-owned devices"),
        ("Crashlytics",         "Real-time crash reporting grouped by build number"),
        ("Performance Monitor", "Startup time, HTTP latency, custom traces from real users"),
        ("Remote Config",       "Feature flags without app update — enable QoE debug mode in test builds"),
        ("Hosting",             "Deploy web player for testing — HTTPS, CDN, instant rollback"),
    ]
    simple_table(slide, ["Service", "Purpose"],
                 rows, Inches(0.5), Inches(1.45), Inches(12.3),
                 col_widths=[Inches(2.8), Inches(9.5)])
    callout_box(slide, "Setup overview",
                "console.firebase.google.com → Add project → Add Android & iOS apps → "
                "Download google-services.json (Android) and GoogleService-Info.plist (iOS) → "
                "Add Firebase SDK to each app.",
                Inches(0.5), Inches(5.4), Inches(12.3), Inches(0.9), "info")
    return slide


def build_firebase_distribution(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Firebase App Distribution — CI Integration")
    h2(slide, "Android", Inches(0.5), Inches(1.4))
    code_box(slide, """- name: Build debug APK
  run: ./gradlew assembleDebug
  working-directory: android-player

- name: Upload to Firebase App Distribution
  uses: wzieba/Firebase-Distribution-Github-Action@v1
  with:
    appId: ${{ secrets.FIREBASE_ANDROID_APP_ID }}
    serviceCredentialsFileContent: >-
      ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
    groups: ci-testers
    file: android-player/app/build/outputs/apk/debug/app-debug.apk
    releaseNotes: "Build #${{ github.run_number }} — ${{ github.sha }}"
""",
    Inches(0.5), Inches(1.85), Inches(6.2), Inches(3.1))
    h2(slide, "iOS", Inches(6.9), Inches(1.4))
    code_box(slide, """- name: Build IPA
  run: |
    xcodebuild archive \\
      -project QoePlayerApp.xcodeproj \\
      -scheme QoePlayerApp \\
      -destination 'generic/platform=iOS' \\
      -archivePath QoePlayerApp.xcarchive
  working-directory: ios-player

- name: Upload to Firebase
  uses: wzieba/Firebase-Distribution-Github-Action@v1
  with:
    appId: ${{ secrets.FIREBASE_IOS_APP_ID }}
    serviceCredentialsFileContent: >-
      ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
    groups: ci-testers
    file: ios-player/QoePlayerApp.xcarchive
""",
    Inches(6.9), Inches(1.85), Inches(5.9), Inches(3.1))
    callout_box(slide, "GitHub Secrets needed",
                "FIREBASE_SERVICE_ACCOUNT (project JSON key), "
                "FIREBASE_ANDROID_APP_ID, FIREBASE_IOS_APP_ID",
                Inches(0.5), Inches(5.2), Inches(12.3), Inches(0.65), "warning")
    return slide


def build_firebase_testlab(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Firebase Test Lab — Real Device Testing")
    code_box(slide, """- name: Install gcloud CLI
  uses: google-github-actions/setup-gcloud@v2
  with:
    service_account_key: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
    project_id: qoe-workshop

- name: Run on Firebase Test Lab
  run: |
    gcloud firebase test android run \\
      --type instrumentation \\
      --app android-player/app/build/outputs/apk/debug/*.apk \\
      --test android-player/app/build/outputs/apk/androidTest/**/*.apk \\
      --device model=Pixel6,version=33,locale=en \\
      --device model=Pixel4,version=30,locale=en \\
      --results-bucket gs://qoe-test-results \\
      --timeout 10m""",
    Inches(0.5), Inches(1.45), Inches(7.5), Inches(4.0))
    simple_table(slide, ["Device", "API Level", "Why"],
        [
            ("Pixel 6",       "33 (Android 13)", "Latest flagship — Widevine L1"),
            ("Pixel 4",       "30 (Android 11)", "Older flagship — broad user base"),
            ("Galaxy S21",    "32 (Android 12)", "Samsung skin — UI compatibility"),
            ("Low-RAM device","28 (Android 9)",  "Memory pressure — OOM testing"),
        ],
        Inches(8.2), Inches(1.45), Inches(4.6),
        col_widths=[Inches(1.5), Inches(1.5), Inches(1.6)])
    return slide


# ── SECTION: GitHub Actions ──────────────────────────────────────────────────

def build_gh_actions_overview(prs):
    slide = blank_slide(prs)
    slide_title(slide, "GitHub Actions — Overview & Core Concepts")
    simple_table(slide, ["Concept", "Description"],
        [
            ("Workflow",  "YAML file in .github/workflows/ — defines when and what to run"),
            ("Event",     "Trigger: push, pull_request, workflow_dispatch, schedule, etc."),
            ("Job",       "A set of steps that run on a single runner (VM)"),
            ("Step",      "Individual task — shell command or reusable Action"),
            ("Action",    "Reusable unit from GitHub Marketplace (e.g. actions/checkout@v4)"),
            ("Runner",    "GitHub-hosted or self-hosted VM that executes jobs"),
            ("Artifact",  "Files persisted between jobs or available for download"),
            ("Secret",    "Encrypted env var at repo/org/environment level"),
            ("Context",   "Runtime data: github.sha, github.ref, github.run_number, etc."),
        ],
        Inches(0.5), Inches(1.45), Inches(12.3),
        col_widths=[Inches(1.8), Inches(10.5)])
    for i, (v, l, t) in enumerate([
        ("Free", "for public repos", "success"),
        ("2,000", "free minutes/month (private)", None),
        ("20+", "GitHub-hosted runner options", None),
    ]):
        stat_box(slide, v, l, Inches(0.5 + i * 4.1), Inches(5.8), Inches(3.8), t)
    return slide


def build_workflow_anatomy(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Workflow File — Full Anatomy")
    code_box(slide, """name: QoE API Tests                    # Display name in GitHub UI

on:                                    # ── TRIGGERS ──────────────────────────
  push:
    branches: [main, develop]
    paths:
      - 'backend-api/**'               # Only run when API code changes
      - '.github/workflows/qoe-api-tests.yml'
  pull_request:
    branches: [main]
    paths: ['backend-api/**']
  workflow_dispatch:                   # Manual trigger button in GitHub UI

env:                                   # ── WORKFLOW-LEVEL ENV VARS ────────────
  SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}

permissions:                           # ── GITHUB TOKEN PERMISSIONS ───────────
  contents: write                      # needed for gh-pages deploy + releases
  pull-requests: write                 # needed to post PR comments

concurrency:                           # ── CANCEL OLD RUNS ───────────────────
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  unit-tests:                          # ── JOB ──────────────────────────────
    name: Unit Tests
    runs-on: ubuntu-latest             # Runner OS
    timeout-minutes: 15               # Kill hung jobs automatically
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '17' }
      - name: Run tests
        run: ./gradlew unitTest
        working-directory: backend-api
      - name: Upload results
        if: always()                   # Run even on test failure
        uses: actions/upload-artifact@v4
        with: { name: unit-results, path: backend-api/build/test-results/ }
""",
    Inches(0.4), Inches(1.4), Inches(12.5), Inches(5.9), size=8)
    return slide


def build_runner_types(prs):
    slide = blank_slide(prs)
    slide_title(slide, "GitHub-Hosted Runners — Types & Costs")
    simple_table(slide, ["Runner Label", "OS", "CPU / RAM", "Use For", "Free Minutes"],
        [
            ("ubuntu-latest",        "Ubuntu 22.04",        "2 core / 7 GB",  "API, web, Android, Docker, Maven, Gradle", "2,000 / mo"),
            ("ubuntu-22.04",         "Ubuntu 22.04 pinned", "2 core / 7 GB",  "Stable OS version requirement",            "2,000 / mo"),
            ("macos-latest",         "macOS 14 (M-series)", "3 core / 7 GB",  "iOS builds, Xcode, swift test",            "200 / mo"),
            ("macos-13",             "macOS 13 (Intel)",    "3 core / 14 GB", "Older Xcode targets",                     "200 / mo"),
            ("windows-latest",       "Windows Server 2022", "2 core / 7 GB",  ".NET, UWP, Windows-specific tests",        "500 / mo"),
        ],
        Inches(0.5), Inches(1.45), Inches(12.3),
        col_widths=[Inches(2.2), Inches(1.9), Inches(1.7), Inches(4.5), Inches(2.0)])
    callout_box(slide, "macOS costs 10x ubuntu",
                "macOS runners consume free minutes at a 10x multiplier. "
                "200 free macOS minutes = ~20 effective minutes. "
                "Use ubuntu-latest for everything except Xcode builds.",
                Inches(0.5), Inches(4.0), Inches(6.0), Inches(0.9), "warning")
    callout_box(slide, "Self-hosted runners",
                "Install the runner agent on your own hardware for Android device farms "
                "or powerful build machines. Label: [self-hosted, linux, x64].",
                Inches(6.8), Inches(4.0), Inches(6.0), Inches(0.9), "info")
    simple_table(slide, ["Larger Runners (paid)", "CPU/RAM", "Best For"],
        [
            ("ubuntu-latest-4-cores",  "4 core / 16 GB", "Parallel Gradle, large Maven builds"),
            ("ubuntu-latest-8-cores",  "8 core / 32 GB", "Docker build + test simultaneously"),
            ("macos-latest-xlarge",    "6 core / 14 GB", "Full Xcode build + test simultaneously"),
        ],
        Inches(0.5), Inches(5.1), Inches(12.3),
        col_widths=[Inches(2.8), Inches(1.8), Inches(7.7)])
    return slide


def build_secrets_permissions(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Permissions, Tokens & Secrets")
    simple_table(slide, ["Permission", "When Needed"],
        [
            ("contents: read",       "Default — checkout code"),
            ("contents: write",      "Push to gh-pages, create releases, push tags"),
            ("pull-requests: write", "Post or update PR comments"),
            ("packages: write",      "Push Docker images to GitHub Container Registry"),
            ("id-token: write",      "OIDC auth with AWS/GCP/Azure — no static secrets"),
        ],
        Inches(0.5), Inches(1.45), Inches(6.0),
        col_widths=[Inches(2.5), Inches(3.5)])
    simple_table(slide, ["Secret Level", "Scope", "Best For"],
        [
            ("Repository",   "Single repo",      "Repo-specific API keys (Slack token)"),
            ("Environment",  "Staging / prod",   "Environment-specific credentials"),
            ("Organisation", "All org repos",    "Shared tokens (npm, Docker Hub)"),
        ],
        Inches(6.8), Inches(1.45), Inches(6.0),
        col_widths=[Inches(1.5), Inches(1.5), Inches(3.0)])
    code_box(slide, """# Set repo secret from terminal
gh secret set SLACK_BOT_TOKEN \\
  --body "$SLACK_BOT_TOKEN" \\
  --repo palsure/DevOpsDays-Workshop

# List secrets (names only — values never shown)
gh secret list --repo palsure/DevOpsDays-Workshop""",
    Inches(0.5), Inches(3.5), Inches(6.0), Inches(1.9))
    callout_box(slide, "Secrets in if: conditions",
                "secrets.X is NOT available in if: expressions. "
                "Map to workflow-level env: vars first, then use env.TOKEN != '' in if:.",
                Inches(6.8), Inches(3.5), Inches(6.0), Inches(0.9), "warning")
    return slide


def build_triggering_builds(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Triggering Builds — All Trigger Types")
    code_box(slide, """on:
  push:                                      # On push to branch
    branches: [main, 'release/**']
    paths: ['backend-api/**']
    tags: ['v*']                             # On version tags

  pull_request:                              # On every PR commit
    types: [opened, synchronize, reopened]
    branches: [main]

  schedule:                                  # Cron — e.g. nightly
    - cron: '0 6 * * 1-5'                   # weekdays 6 AM UTC

  workflow_dispatch:                         # Manual trigger with inputs
    inputs:
      environment:
        description: 'Target environment'
        type: choice
        options: [staging, production]
        default: staging
      create_release:
        type: boolean
        default: false""",
    Inches(0.5), Inches(1.45), Inches(6.2), Inches(4.5))
    code_box(slide, """# Trigger from terminal
gh workflow run build-acceptance-release.yml \\
  --ref main \\
  --field environment=production \\
  --field create_release=true

# List recent runs
gh run list --workflow=qoe-api-tests.yml

# Watch live output
gh run watch

# Cancel a running workflow
gh run cancel 1234567890""",
    Inches(6.9), Inches(1.45), Inches(5.9), Inches(2.8))
    simple_table(slide, ["Status", "Meaning", "Action"],
        [
            ("queued",      "Waiting for runner",                  "Normal — 10–30 s"),
            ("in_progress", "Runner executing",                    "Watch logs live"),
            ("success",     "All steps passed",                    "Proceed with merge"),
            ("failure",     "One or more steps failed",            "Fix and re-push"),
            ("cancelled",   "Manually cancelled or superseded",    "Re-trigger if needed"),
            ("skipped",     "if: condition was false",             "Expected — module unchanged"),
            ("timed_out",   "Exceeded timeout-minutes",            "Check for hung process"),
        ],
        Inches(6.9), Inches(4.5), Inches(5.9),
        col_widths=[Inches(1.3), Inches(2.3), Inches(2.3)], font_size=9)
    return slide


def build_branch_protection(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Branch Protection Rules — Enforce CI Before Merge")
    simple_table(slide, ["Setting", "Recommended Value"],
        [
            ("Branch name pattern",                   "main"),
            ("Require status checks to pass",         "Enabled"),
            ("Required checks",                       "Quality Gate, QoE E2E Gates (Docker stack)"),
            ("Require branches to be up to date",     "Enabled — prevents stale-base merges"),
            ("Require conversation resolution",       "Enabled"),
            ("Restrict who can push to main",         "Admins or named teams only"),
            ("Allow force pushes",                    "Disabled"),
            ("Allow deletions",                       "Disabled"),
        ],
        Inches(0.5), Inches(1.45), Inches(7.5),
        col_widths=[Inches(3.8), Inches(3.7)])
    h2(slide, "Finding Required Status Check Names", Inches(8.4), Inches(1.4))
    code_box(slide, """Workflow: qoe-validation.yml
  Job name: quality-gate
  Status check: "Quality Gate"

Workflow: qoe-pr-e2e.yml
  Job name: e2e
  Status check: "QoE E2E Gates (Docker stack)"

→ Add these exact strings to the
  Required status checks field in
  Settings → Branches → Add Rule""",
    Inches(8.4), Inches(1.85), Inches(4.5), Inches(3.0))
    callout_box(slide, "Settings → Branches → Add Rule",
                "Path: github.com/{owner}/{repo}/settings/branches",
                Inches(0.5), Inches(5.5), Inches(12.3), Inches(0.7), "info")
    return slide


def build_release_process(prs):
    slide = blank_slide(prs)
    slide_title(slide, "Release Process — End to End")
    code_box(slide, """
Developer merges PR to main
  │   (qoe-validation.yml + qoe-pr-e2e.yml already passed — branch protection enforced)
  ▼
Release manager triggers build-acceptance-release.yml (workflow_dispatch)
  │
  ├─ changes job: dorny/paths-filter — detect changed modules since last tag
  │
  ├─ [api / web / android / ios / automation]-acceptance jobs (parallel)
  │      Each: checkout → docker compose up → full test suite → POST results to gate API
  │
  ├─ quality-gate job
  │      POST /api/v1/pipeline-runs/{id}/finalize
  │      { "status": "RELEASED", "passRate": 0.94 }  ← >= 80% passes
  │      Sends Slack acceptance result
  │
  │   PASSED                                   FAILED
  │     │                                        │
  │   release job                          Slack alert + block deploy
  │     │
  │   gh release create v2026.04.26-{run_number}
  │     --generate-notes (auto-changelog from PR titles)
  │     --latest
  │     Attach: build-manifest.json
  │
  ▼
GitHub Release published → Slack release announcement
  │
  ▼
Deploy job (environment: production → requires reviewer approval)
  │
  ▼
Smoke tests on production endpoint + New Relic alert baseline check
""",
    Inches(0.4), Inches(1.4), Inches(12.5), Inches(5.9), size=8)
    return slide


def build_gh_actions_troubleshooting(prs):
    slide = blank_slide(prs)
    slide_title(slide, "GitHub Actions — Common Errors & Fixes")
    rows = [
        ("Workflow not triggered",             "paths: filter doesn't match",         "Add self-referential workflow file to paths:"),
        ("Resource not accessible",            "GITHUB_TOKEN lacks permission",        "Add permissions: contents: write to workflow"),
        ("'Context access invalid: secrets'",  "secrets.X in if: condition",          "Map to env: var; use env.VAR != '' in if:"),
        ("actions/setup-android not found",    "Wrong action namespace",              "Use android-actions/setup-android@v2"),
        ("No space left on device",            "Large build fills 14 GB runner disk", "Add: sudo rm -rf /usr/share/dotnet /opt/ghc"),
        ("Job skipped unexpectedly",           "if: condition resolved false",        "Echo inputs/context to debug the condition"),
        ("Cache miss every run",               "hashFiles() path matches nothing",    "Verify path with ls before caching"),
        ("Artifact download fails",            "Name mismatch or upload skipped",     "if: always() on upload; verify artifact names"),
        ("xcodebuild exit code lost",          "Pipe to xcpretty without pipefail",   "Add set -o pipefail before xcodebuild | xcpretty"),
        ("Docker port already in use",         "Previous run leaked containers",       "docker compose down -v in always-run teardown"),
        ("Playwright browser not found",       "Browsers not installed",              "npx playwright install --with-deps chromium"),
    ]
    simple_table(slide, ["Error / Symptom", "Root Cause", "Fix"],
                 rows, Inches(0.4), Inches(1.45), Inches(12.5),
                 col_widths=[Inches(3.0), Inches(3.3), Inches(6.2)], font_size=8)
    return slide


# ─── Build all slides ─────────────────────────────────────────────────────────

def build_all(prs):
    builders = [
        # Introduction
        build_title_slide,          # 1
        build_agenda,               # 2
        build_qoe_overview,         # 3
        # Platforms
        build_platforms_overview,   # 4
        build_platform_stacks,      # 5
        build_video_delivery,       # 6
        # Quality Impact
        build_quality_impact,       # 7
        build_qoe_scoring,          # 8
        # Test Types
        build_test_pyramid,         # 9
        build_test_types,           # 10
        build_acceptance_tests,     # 11
        build_smoke_tests,          # 12
        build_regression_tests,     # 13
        # CI/CD Benefits
        build_cicd_benefits,        # 14
        build_path_filtering,       # 15
        # Pipeline Architecture
        build_arch_overview,        # 16
        build_quality_gate,         # 17
        build_fallback_options,     # 18
        build_slack_arch,           # 19
        # Slack Bot Setup
        build_slack_setup,          # 20
        build_slack_blockkit,       # 21
        # Firebase
        build_firebase_overview,    # 22
        build_firebase_distribution,# 23
        build_firebase_testlab,     # 24
        # GitHub Actions
        build_gh_actions_overview,  # 25
        build_workflow_anatomy,     # 26
        build_runner_types,         # 27
        build_secrets_permissions,  # 28
        build_triggering_builds,    # 29
        build_branch_protection,    # 30
        build_release_process,      # 31
        build_gh_actions_troubleshooting,  # 32
    ]
    total = len(builders)
    slides = []
    for i, fn in enumerate(builders, start=1):
        slide = fn(prs)
        slide_number(slide, i, total)
        slides.append(slide)
        print(f"  [{i:02d}/{total}] {fn.__name__}")
    return slides


def main():
    print("Building DevOpsDays QoE Workshop presentation...")
    prs = new_prs()
    build_all(prs)
    out = os.path.join(os.path.dirname(__file__), "DevOpsDays-QoE-Workshop.pptx")
    prs.save(out)
    print(f"\nSaved: {out}")
    print(f"Slides: {len(prs.slides)}")

if __name__ == "__main__":
    main()
