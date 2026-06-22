#!/usr/bin/env python3
"""
Literature Processing Skill - Core Module (Fixed)
"""

import os
import re
import json
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import fitz


class PDFType(Enum):
    ACADEMIC = "academic"
    DISSERTATION = "dissertation"
    BOOK = "book"
    POLICY = "policy"
    UNKNOWN = "unknown"


class PDFQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    ENCRYPTED = "encrypted"
    CNKI_GARBLED = "cnki_garbled"


@dataclass
class PDFAnalysis:
    file_path: str
    file_hash: str
    pdf_type: PDFType
    quality: PDFQuality
    page_count: int = 0
    has_text_layer: bool = False
    is_encrypted: bool = False
    is_columar: bool = False
    column_count: int = 1
    metadata: Dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class Heading:
    level: int
    title: str
    page: int
    bbox: Tuple[float, float, float, float]
    font_size: float
    is_bold: bool


@dataclass
class Section:
    level: int
    title: str
    content: str
    start_page: int
    end_page: int
    word_count: int
    children: List['Section'] = field(default_factory=list)


class PDFClassifier:
    DISSERTATION_PATTERNS = [
        r"DOCTORAL?\s*DISSERTATION",
        r"MASTER'?S?\s*THESIS",
        r"Dissertation",
        r"Thesis",
        r"研究生",
        r"毕业论文",
        r"答辩",
        r"指导教师",
        r"导师",
    ]

    POLICY_PATTERNS = [
        r"国发\s*\[",
        r"国办发\s*\[",
        r"StateCouncil",
        r"MOHURD",
        r"Notice",
        r"Opinion",
        r"Regulation",
        r"Ordinance",
    ]

    BOOK_PATTERNS = [
        r"出版社",
        r"ISBN",
        r"版次",
        r"印刷",
        r"定价",
        r"主编",
        r"副主编",
        r"丛书",
        r"Chapter\s+\d+",
    ]

    @classmethod
    def classify(cls, text_sample: str, metadata: Dict) -> PDFType:
        dissertation_score = sum(1 for p in cls.DISSERTATION_PATTERNS
                                   if re.search(p, text_sample, re.I))
        policy_score = sum(1 for p in cls.POLICY_PATTERNS
                           if re.search(p, text_sample, re.I))
        book_score = sum(1 for p in cls.BOOK_PATTERNS
                         if re.search(p, text_sample, re.I))
        academic_indicators = [
            r"Abstract", r"摘要", r"Keywords?", r"关键词",
            r"Introduction", r"引言", r"参考文献", r"References",
        ]
        academic_score = sum(1 for p in academic_indicators
                             if re.search(p, text_sample, re.I))

        scores = {
            PDFType.DISSERTATION: dissertation_score * 2,
            PDFType.POLICY: policy_score * 2,
            PDFType.BOOK: book_score * 1.5,
            PDFType.ACADEMIC: academic_score,
        }

        max_type = max(scores, key=scores.get)
        return max_type if scores[max_type] >= 2 else PDFType.UNKNOWN


class PDFQualityChecker:
    @staticmethod
    def check_quality(doc: fitz.Document, sample_text: str) -> Tuple[PDFQuality, List[str]]:
        warnings = []

        if doc.is_encrypted:
            return PDFQuality.ENCRYPTED, ["PDF encrypted"]

        if PDFQualityChecker._is_cnki_garbled(sample_text):
            return PDFQuality.CNKI_GARBLED, ["CNKI garbled PDF"]

        total_chars = len(sample_text)
        if total_chars < 100:
            warnings.append("Text layer nearly empty")
            return PDFQuality.POOR, warnings

        garbled = PDFQualityChecker._count_garbled(sample_text[:1000])
        if garbled > 0.3:
            return PDFQuality.POOR, warnings

        if garbled < 0.05:
            return PDFQuality.EXCELLENT, warnings

        return PDFQuality.GOOD, warnings

    @staticmethod
    def _is_cnki_garbled(text: str) -> bool:
        if not text:
            return False
        if text.count('�') > 10:
            return True
        return False

    @staticmethod
    def _count_garbled(text: str) -> float:
        if not text:
            return 0.0
        control_chars = len(re.findall(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', text))
        return control_chars / len(text) if text else 0.0


class SmartHeadingExtractor:
    """Smart heading extractor that filters headers/footers"""

    HEADER_FOOTER_PATTERNS = [
        r"^\s*博士学位论文\s*$",
        r"^\s*硕士学位论文\s*$",
        r"^\s*第\s*\d+\s*页\s*$",
        r"^\s*Page\s*\d+\s*$",
        r"^\s*\d{1,3}\s*$",
        r"^\s*Chapter\s*\d+\s*$",
        r"^\s*申请学位类别\s*$",
        r"^\s*学位授予单位\s*$",
        r"^\s*东\s*南\s*大\s*学\s*$",
        r"^\s*研究生姓名\s*[:：]?\s*$",
        r"^\s*导师姓名\s*[:：]?\s*$",
        r"^\s*专\s*$",
        r"^\s*业\s*$",
        r"^\s*名\s*$",
        r"^\s*称\s*$",
        r"^\s*导\s*$",
        r"^\s*师\s*$",
        r"^\s*[:：]\s*$",
    ]

    CHAPTER_PATTERNS = [
        (1, r"^\s*第\s*[一二三四五六七八九十\d]+\s*章\s+.+"),
        (2, r"^\s*\d+\.\d+\s+[^.\d].+"),
        (3, r"^\s*\d+\.\d+\.\d+\s+.+"),
        (1, r"^\s*Chapter\s+\d+\s*[:\-]?\s*.+", re.I),
        (1, r"^\s*\d+\s+[A-Z][^a-z]{2,}"),
    ]

    def __init__(self):
        self.min_heading_font = 11.0

    def extract_headings(self, doc: fitz.Document) -> List[Heading]:
        """Extract headings using simple text mode (more reliable for Chinese PDFs)"""
        all_headings = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            # Use simple text extraction instead of dict mode
            page_headings = self._extract_headings_from_text(page, page_num + 1)
            all_headings.extend(page_headings)

        filtered = self._filter_headers_footers(all_headings)
        return self._deduplicate_and_sort(filtered)

    def _extract_headings_from_text(self, page: fitz.Page, page_num: int) -> List[Heading]:
        """Extract headings by analyzing page text lines"""
        headings = []
        text = page.get_text()
        lines = text.split('\n')

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            level = self._detect_heading_level(stripped, 12, False)
            if level > 0:
                headings.append(Heading(
                    level=level,
                    title=stripped,
                    page=page_num,
                    bbox=(0, 0, 0, 0),
                    font_size=12,
                    is_bold=False
                ))

        return headings

    def _detect_heading_level(self, text: str, font_size: float, is_bold: bool) -> int:
        if len(text) < 3 or len(text) > 100:
            return 0

        for level, pattern, *flags in self.CHAPTER_PATTERNS:
            if re.match(pattern, text, flags[0] if flags else 0):
                return level

        return 0

    def _filter_headers_footers(self, headings: List[Heading]) -> List[Heading]:
        filtered = []

        for h in headings:
            is_header_footer = False
            for pattern in self.HEADER_FOOTER_PATTERNS:
                if re.match(pattern, h.title, re.I):
                    is_header_footer = True
                    break

            # Keep section numbers like "1.1", "2.3.1" even if short
            is_section_number = re.match(r'^\s*\d+(\.\d+)*\s+', h.title)

            if len(h.title) < 5 and not is_section_number:
                if not re.match(r'^\s*第', h.title):
                    is_header_footer = True

            if not is_header_footer:
                filtered.append(h)

        return filtered

    def _deduplicate_and_sort(self, headings: List[Heading]) -> List[Heading]:
        seen = set()
        result = []

        for h in headings:
            key = (h.title.lower().strip(), h.page)
            if key not in seen:
                seen.add(key)
                result.append(h)

        return sorted(result, key=lambda x: (x.page, x.bbox[1]))


class ColumnDetector:
    @staticmethod
    def detect_columns(page: fitz.Page) -> Tuple[bool, int]:
        blocks = page.get_text("blocks")
        if len(blocks) < 4:
            return False, 1

        y_groups = {}
        for block in blocks:
            x0, y0, x1, y1, text = block[:5]
            if not text.strip():
                continue
            y_key = int(y0 / 20) * 20
            if y_key not in y_groups:
                y_groups[y_key] = []
            y_groups[y_key].append((x0, x1))

        multi_column_rows = 0
        for y, x_ranges in y_groups.items():
            if len(x_ranges) >= 2:
                x_ranges.sort()
                gaps = [x_ranges[i+1][0] - x_ranges[i][1]
                        for i in range(len(x_ranges)-1)]
                if gaps and min(gaps) > 50:
                    multi_column_rows += 1

        is_columar = multi_column_rows > len(y_groups) * 0.3

        column_count = 1
        if is_columar:
            avg_blocks = sum(len(x) for x in y_groups.values()) / len(y_groups) if y_groups else 1
            column_count = max(2, int(avg_blocks))

        return is_columar, column_count

    @staticmethod
    def reconstruct_reading_order(page: fitz.Page, column_count: int) -> str:
        blocks = page.get_text("blocks")
        page_width = page.rect.width
        col_width = page_width / column_count

        column_blocks = [[] for _ in range(column_count)]
        for block in blocks:
            x0 = block[0]
            col_idx = min(int(x0 / col_width), column_count - 1)
            column_blocks[col_idx].append(block)

        text_parts = []
        for col_blocks in column_blocks:
            col_blocks.sort(key=lambda b: b[1])
            for block in col_blocks:
                text_parts.append(block[4])

        return '\n'.join(text_parts)


class GrobidExtractor:
    def __init__(self, base_url: str = "http://127.0.0.1:8070"):
        self.base_url = base_url.rstrip('/')

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/isalive", timeout=5)
            return response.status_code == 200 and response.text.strip() == "true"
        except:
            return False

    def extract(self, pdf_path: str) -> Optional[Dict]:
        if not self.is_available():
            return None

        try:
            with open(pdf_path, 'rb') as f:
                files = {'input': f}
                response = requests.post(
                    f"{self.base_url}/api/processFulltextDocument",
                    files=files,
                    timeout=120
                )

            if response.status_code == 200:
                return self._parse_tei(response.text)
            else:
                return {"error": f"Grobid returned {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    def _parse_tei(self, tei_xml: str) -> Dict:
        result = {
            "title": self._extract_tag(tei_xml, "title"),
            "abstract": self._extract_tag(tei_xml, "abstract"),
            "body": self._extract_body(tei_xml),
            "sections": self._extract_sections(tei_xml),
        }
        return result

    def _extract_tag(self, xml: str, tag: str) -> str:
        pattern = f'<{tag}[^>]*>(.*?)</{tag}>'
        match = re.search(pattern, xml, re.DOTALL | re.I)
        return re.sub(r'<[^>]+>', '', match.group(1)) if match else ""

    def _extract_body(self, xml: str) -> str:
        match = re.search(r'<body[^>]*>(.*?)</body>', xml, re.DOTALL | re.I)
        return re.sub(r'<[^>]+>', ' ', match.group(1)).strip() if match else ""

    def _extract_sections(self, xml: str) -> List[Dict]:
        sections = []
        pattern = r'<div[^>]*>.*?<head[^>]*>(.*?)</head>.*?</div>'
        for match in re.finditer(pattern, xml, re.DOTALL | re.I):
            title = re.sub(r'<[^>]+>', '', match.group(1))
            sections.append({"title": title, "level": 1})
        return sections
