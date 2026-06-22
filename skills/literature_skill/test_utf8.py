#!/usr/bin/env python3
"""
文献智能处理 Skill - 核心模块
提供PDF分类、提取、分块功能
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
import fitz  # PyMuPDF


class PDFType(Enum):
    """PDF文献类型"""
    ACADEMIC = "academic"           # 学术论文
    DISSERTATION = "dissertation"  # 学位论文
    BOOK = "book"                   # 专著/书籍
    POLICY = "policy"               # 政策文件
    UNKNOWN = "unknown"             # 未知类型


class PDFQuality(Enum):
    """PDF质量评估"""
    EXCELLENT = "excellent"  # 文本层完整
    GOOD = "good"            # 可提取，需处理
    POOR = "poor"            # 扫描件/OCR质量差
    ENCRYPTED = "encrypted"  # 加密/无法读取
    CNKI_GARBLED = "cnki_garbled"  # 知网乱码PDF


@dataclass
class PDFAnalysis:
    """PDF分析结果"""
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
    """文档标题结构"""
    level: int
    title: str
    page: int
    bbox: Tuple[float, float, float, float]
    font_size: float
    is_bold: bool


@dataclass
class DocumentChunk:
    """文档分块"""
    chunk_id: str
    heading: Optional[Heading]
    content: str
    start_page: int
    end_page: int
    word_count: int
