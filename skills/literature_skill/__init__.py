#!/usr/bin/env python3
"""
文献智能处理 Skill - 主处理器 (Fixed)
按章节生成独立MD文件
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from core import (
    PDFType, PDFQuality, PDFAnalysis, Heading, Section,
    PDFClassifier, PDFQualityChecker, ColumnDetector,
    SmartHeadingExtractor, GrobidExtractor
)

import fitz  # PyMuPDF


class LiteratureProcessor:
    """文献处理器 - 按章节生成独立MD文件"""

    def __init__(self, output_dir: str = "./processed", grobid_url: str = "http://127.0.0.1:8070"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.grobid = GrobidExtractor(grobid_url)
        self.heading_extractor = SmartHeadingExtractor()

    def process(self, pdf_path: str, force: bool = False) -> Dict:
        """处理PDF，按章节生成独立MD文件"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return {"error": f"文件不存在: {pdf_path}"}

        file_hash = self._compute_hash(pdf_path)

        # 分析PDF
        print(f"[INFO] 分析PDF: {pdf_path.name}")
        analysis = self._analyze_pdf(pdf_path)

        if analysis.quality in [PDFQuality.ENCRYPTED, PDFQuality.CNKI_GARBLED]:
            return self._create_intervention_request(analysis)

        print(f"[INFO] 类型: {analysis.pdf_type.value}, 页数: {analysis.page_count}")

        # 提取文本和标题
        extraction = self._extract_text(pdf_path, analysis)

        # 按章节分割并生成文件
        sections = self._split_by_sections(extraction)

        # 生成章节MD文件
        section_files = self._generate_section_files(sections, pdf_path, analysis)

        # 生成结果
        result = {
            "meta": {
                "file": str(pdf_path),
                "file_hash": file_hash,
                "processed_at": datetime.now().isoformat(),
            },
            "analysis": {
                "pdf_type": analysis.pdf_type.value,
                "quality": analysis.quality.value,
                "page_count": analysis.page_count,
            },
            "sections": [
                {
                    "index": s["index"],
                    "title": s["title"],
                    "level": s["level"],
                    "pages": s["pages"],
                    "word_count": s["word_count"],
                    "filename": s["filename"]
                }
                for s in section_files
            ],
            "output_dir": str(self.output_dir / f"{pdf_path.stem}_sections")
        }

        # 保存索引文件
        index_file = self.output_dir / f"{pdf_path.stem}_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 处理完成! 生成 {len(section_files)} 个章节文件")
        print(f"[OK] 索引文件: {index_file}")

        return result

    def _analyze_pdf(self, pdf_path: Path) -> PDFAnalysis:
        """分析PDF"""
        doc = fitz.open(pdf_path)

        sample_pages = min(3, len(doc))
        sample_text = ""
        for i in range(sample_pages):
            sample_text += doc[i].get_text()

        pdf_type = PDFClassifier.classify(sample_text, doc.metadata)
        quality, warnings = PDFQualityChecker.check_quality(doc, sample_text)

        is_columar, column_count = False, 1
        if len(doc) > 0:
            is_columar, column_count = ColumnDetector.detect_columns(doc[0])

        has_text = len(sample_text.strip()) > 50

        page_count = len(doc)
        is_encrypted = doc.is_encrypted
        metadata = dict(doc.metadata)

        doc.close()

        return PDFAnalysis(
            file_path=str(pdf_path),
            file_hash=self._compute_hash(pdf_path),
            pdf_type=pdf_type,
            quality=quality,
            page_count=page_count,
            has_text_layer=has_text,
            is_encrypted=is_encrypted,
            is_columar=is_columar,
            column_count=column_count,
            metadata=metadata,
            warnings=warnings
        )

    def _extract_text(self, pdf_path: Path, analysis: PDFAnalysis) -> Dict:
        """提取文本和标题 - 直接从正文提取，跳过目录"""
        doc = fitz.open(pdf_path)

        # 首先找到正文开始的位置（绪论或第一章）
        content_start_page = self._find_content_start(doc)
        print(f"[INFO] 正文从第 {content_start_page} 页开始")

        # 从正文开始提取标题
        headings = self._extract_headings_from_content(doc, content_start_page)
        print(f"[INFO] 从正文提取到 {len(headings)} 个章节标题")

        # 提取所有页面的文本（带页码标记）
        pages_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]

            if analysis.is_columar:
                text = ColumnDetector.reconstruct_reading_order(page, analysis.column_count)
            else:
                text = page.get_text()

            # 提取页码标记
            page_marker = self._extract_page_marker(text)

            pages_text.append({
                "page_num": page_num + 1,
                "page_marker": page_marker,
                "text": text
            })

        doc.close()

        return {
            "pages": pages_text,
            "headings": headings,
            "content_start_page": content_start_page
        }

    def _find_content_start(self, doc: fitz.Document) -> int:
        """找到正文开始的位置 - 绪论开始的地方"""
        # 从第3页开始查找（跳过封面）
        for page_num in range(3, min(len(doc), 20)):
            text = doc[page_num].get_text()
            # 查找绪论或第0章或第1章
            if re.search(r'第\s*0\s*章|绪论|0\.1\s+', text):
                return page_num + 1
            # 如果没找到绪论，找第一章
            if re.search(r'第\s*一\s*章', text):
                dot_count = text.count('.')
                if dot_count < 50:
                    return page_num + 1
        return 1

    def _extract_headings_from_content(self, doc: fitz.Document, start_page: int) -> List[Dict]:
        """提取主节标题（只提取第X章和X.X，不包含X.X.X），记录精确位置"""
        headings = []
        last_chapter_title = None
        last_section_title = None

        for page_num in range(start_page - 1, len(doc)):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split('\n')

            line_offset = 0  # 记录行位置
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    line_offset += len(line) + 1  # +1 for newline
                    continue

                # 检查是否是主节标题
                level = self._detect_main_heading(stripped)
                if level > 0:
                    # 过滤目录项
                    if stripped.count('.') > 10:
                        line_offset += len(line) + 1
                        continue

                    clean_title = self._clean_heading(stripped)

                    # 去重：同一标题在同一页或相邻页只保留一次
                    if level == 1:
                        if clean_title == last_chapter_title:
                            line_offset += len(line) + 1
                            continue
                        last_chapter_title = clean_title
                    elif level == 2:
                        if clean_title == last_section_title:
                            line_offset += len(line) + 1
                            continue
                        last_section_title = clean_title

                    headings.append({
                        "level": level,
                        "title": clean_title,
                        "page": page_num + 1,
                        "line_pos": line_offset,  # 行内偏移位置
                        "page_text": text,  # 保存页面文本用于后续分割
                    })

                line_offset += len(line) + 1

        return headings

    def _detect_main_heading(self, text: str) -> int:
        """只检测主节标题（第X章或X.X，不检测X.X.X），过滤表格数字行"""
        # 首先过滤明显不是标题的情况
        # 过滤纯数字+单位开头的行（表格数据）
        if re.match(r'^\s*\d+\.\d+\s*(平方公里|km2?|米|公顷|平方米|%|页|图|表)', text):
            return 0
        # 过滤只有数字和标点的短行
        if re.match(r'^\s*\d+\.\d+[^一-龥]*$', text):  # 没有中文字符
            return 0
        # 过滤包含多个数字和单位的行（表格数据）
        if len(re.findall(r'\d+\.?\d*\s*(平方公里|km|米|公顷|%)', text)) >= 2:
            return 0

        # 第X章（一级标题）
        if re.match(r'^\s*第\s*[一二三四五六七八九十]+\s*章\s+', text):
            return 1
        # 绪论（特殊的一级标题）
        if re.match(r'^\s*绪论\s*$', text) or re.match(r'^\s*第\s*0\s*章', text):
            return 1
        # X.X 节（二级标题）- 确保不是X.X.X
        if re.match(r'^\s*\d+\.\d+\s+[^.\d]', text):
            # 进一步检查不是X.X.X
            if not re.match(r'^\s*\d+\.\d+\.\d+', text):
                # 检查是否有足够的中文字符（至少3个）
                chinese_chars = re.findall(r'[一-龥]', text)
                if len(chinese_chars) >= 3:
                    return 2
            # 0.X 绪论小节也算二级
            if re.match(r'^\s*0\.\d+\s+', text):
                return 2
        return 0

    def _clean_heading(self, text: str) -> str:
        """清理标题"""
        # 移除末尾的页码和点
        text = re.sub(r'\s+\d+\s*$', '', text)
        text = re.sub(r'\s+\.\.+\s*\d*\s*$', '', text)
        return text.strip()

    def _extract_page_marker(self, text: str) -> Optional[int]:
        """提取页码标记（如页眉页脚中的数字）"""
        lines = text.split('\n')
        for line in lines[:5]:  # 检查前5行
            match = re.match(r'^\s*(\d+)\s*$', line.strip())
            if match:
                return int(match.group(1))
        return None

    def _split_by_sections(self, extraction: Dict) -> List[Dict]:
        """按标题分割内容为章节 - 使用精确位置而非整页"""
        pages = extraction["pages"]
        headings = extraction["headings"]

        if not headings:
            all_text = "\n".join(p["text"] for p in pages)
            return [{
                "level": 1,
                "title": "正文",
                "content": all_text,
                "start_page": 1,
                "end_page": len(pages)
            }]

        # 为每个标题构建位置信息（页码+行内偏移）
        heading_positions = []
        for h in headings:
            # 找到该标题在完整文本中的起始位置
            pos = self._find_heading_position(pages, h["page"], h["title"])
            heading_positions.append({
                "level": h["level"],
                "title": h["title"],
                "page": h["page"],
                "line_pos": h.get("line_pos", 0),
                "abs_pos": pos
            })

        sections = []
        total_pages = len(pages)

        for i, h in enumerate(heading_positions):
            start_page = h["page"]
            start_line_pos = h.get("line_pos", 0)

            if i < len(heading_positions) - 1:
                next_h = heading_positions[i + 1]
                end_page = next_h["page"]
                end_line_pos = next_h.get("line_pos", 0)
            else:
                end_page = total_pages
                end_line_pos = -1  # 到末尾

            # 提取这个精确位置范围的内容
            content = self._extract_content_by_position(
                pages, start_page, start_line_pos, end_page, end_line_pos
            )
            content = self._clean_text(content)

            sections.append({
                "level": h["level"],
                "title": h["title"],
                "content": content,
                "start_page": start_page,
                "end_page": end_page if end_line_pos == -1 else end_page - 1
            })

        return sections

    def _find_heading_position(self, pages: List[Dict], page_num: int, title: str) -> int:
        """找到标题在页面文本中的位置"""
        abs_pos = 0
        for p in pages:
            if p["page_num"] == page_num:
                text = p["text"]
                # 在页面文本中查找标题
                idx = text.find(title)
                if idx >= 0:
                    return abs_pos + idx
                return abs_pos
            abs_pos += len(p["text"]) + 1
        return abs_pos

    def _extract_content_by_position(
        self, pages: List[Dict],
        start_page: int, start_line_pos: int,
        end_page: int, end_line_pos: int
    ) -> str:
        """根据精确位置提取内容"""
        content_parts = []

        for p in pages:
            page_num = p["page_num"]

            if page_num < start_page:
                continue
            if page_num > end_page:
                break

            text = p["text"]
            lines = text.split('\n')

            if page_num == start_page and page_num == end_page:
                # 开始和结束在同一页
                # 从start_line_pos到end_line_pos
                pos = 0
                start_abs = None
                end_abs = len(text)
                for line in lines:
                    line_len = len(line) + 1  # +1 for newline
                    if pos <= start_line_pos < pos + line_len:
                        start_abs = pos
                    if end_line_pos > 0 and pos <= end_line_pos < pos + line_len:
                        end_abs = pos
                        break
                    pos += line_len

                if start_abs is not None:
                    content_parts.append(text[start_abs:end_abs])
                else:
                    content_parts.append(text)

            elif page_num == start_page:
                # 开始页 - 从start_line_pos到末尾
                pos = 0
                start_abs = None
                for line in lines:
                    line_len = len(line) + 1
                    if pos <= start_line_pos < pos + line_len:
                        start_abs = pos
                        break
                    pos += line_len

                if start_abs is not None:
                    content_parts.append(text[start_abs:])
                else:
                    content_parts.append(text)

            elif page_num == end_page:
                # 结束页 - 从开头到end_line_pos
                if end_line_pos == -1:
                    content_parts.append(text)
                else:
                    pos = 0
                    end_abs = len(text)
                    for line in lines:
                        line_len = len(line) + 1
                        if pos <= end_line_pos < pos + line_len:
                            end_abs = pos
                            break
                        pos += line_len
                    content_parts.append(text[:end_abs])

            else:
                # 中间页 - 整页
                content_parts.append(text)

        return '\n'.join(content_parts)

    def _normalize(self, text: str) -> str:
        """标准化文本用于比较"""
        return re.sub(r'\s+', '', text.strip().lower())

    def _clean_text(self, text: str) -> str:
        """清理文本 - 过滤页眉页脚"""
        lines = text.split('\n')
        cleaned = []

        # 页眉页脚过滤模式
        header_patterns = [
            r'^\s*东南大学博士学位论文\s*$',
            r'^\s*东南大学硕士学位论文\s*$',
            r'^\s*第\s*\d+\s*页\s*$',
            r'^\s*\d{1,3}\s*$',  # 单独的数字页码
            r'^\s*第[一二三四五六七八九十]+章.*$',  # 页眉中的章标题
        ]

        prev_line = None
        prev_empty = True
        for line in lines:
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                if not prev_empty:
                    cleaned.append('')
                    prev_empty = True
                continue

            prev_empty = False

            # 检查是否是页眉页脚
            is_header = False
            for pattern in header_patterns:
                if re.match(pattern, stripped):
                    is_header = True
                    break

            if not is_header:
                cleaned.append(stripped)
                prev_line = stripped

        return '\n'.join(cleaned)

    def _generate_section_files(self, sections: List[Dict], pdf_path: Path, analysis: PDFAnalysis) -> List[Dict]:
        """为每个章节生成MD文件"""
        base_name = pdf_path.stem
        sections_dir = self.output_dir / f"{base_name}_sections"
        sections_dir.mkdir(exist_ok=True)

        generated = []

        for i, section in enumerate(sections):
            # 生成文件名
            safe_title = self._safe_filename(section['title'])
            filename = f"{i+1:03d}_{safe_title}.md"
            filepath = sections_dir / filename

            # 构建内容
            lines = []
            lines.append("---")
            lines.append(f'title: "{section["title"]}"')
            lines.append(f"source_pdf: {pdf_path.name}")
            lines.append(f"section_level: {section['level']}")
            lines.append(f"pdf_type: {analysis.pdf_type.value}")
            lines.append(f"pages: {section['start_page']}-{section['end_page']}")
            lines.append(f"word_count: {len(section['content'])}")
            lines.append("---")
            lines.append("")

            # 添加章节标题和内容
            lines.append(f"{'#' * section['level']} {section['title']}")
            lines.append("")
            lines.append(section['content'])

            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            generated.append({
                "index": i + 1,
                "title": section['title'],
                "level": section['level'],
                "pages": f"{section['start_page']}-{section['end_page']}",
                "word_count": len(section['content']),
                "filename": filename,
                "filepath": str(filepath)
            })

        return generated

    def _safe_filename(self, text: str) -> str:
        """转换为安全文件名"""
        safe = re.sub(r'[<>:"/\\|?*]', '', text)
        safe = re.sub(r'\s+', '_', safe)
        safe = safe.strip('._')
        if not safe:
            safe = "section"
        return safe[:40]

    def _create_intervention_request(self, analysis: PDFAnalysis) -> Dict:
        return {
            "status": "requires_intervention",
            "file": analysis.file_path,
            "reason": analysis.quality.value
        }

    def _compute_hash(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="文献智能处理 - 按章节生成独立MD文件"
    )
    parser.add_argument("pdf", help="PDF文件路径")
    parser.add_argument("-o", "--output", default="./processed",
                       help="输出目录")
    parser.add_argument("--grobid-url", default="http://127.0.0.1:8070",
                       help="Grobid服务地址")
    parser.add_argument("-f", "--force", action="store_true",
                       help="强制重新处理")

    args = parser.parse_args()

    processor = LiteratureProcessor(
        output_dir=args.output,
        grobid_url=args.grobid_url
    )

    result = processor.process(args.pdf, force=args.force)

    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
