"""
Paper Memory Manager - 论文记忆管理 Skill

增量读取 DOCX 章节并同步到记忆文件。
"""

from .core import HeadingDetector, SectionExtractor, MemoryUpdater
from pathlib import Path
from typing import Dict, List, Optional
import datetime


class PaperMemoryManager:
    """
    论文记忆管理器 - 处理 DOCX 增量读取和记忆更新
    """

    def __init__(self, memory_dir: str = "./wiki/meta"):
        """
        初始化管理器

        Args:
            memory_dir: 记忆文件存放目录
        """
        self.memory_dir = Path(memory_dir)
        self.detector = HeadingDetector()
        self.extractor = SectionExtractor()
        self.updater = MemoryUpdater()

    def update_section(
        self,
        docx_path: str,
        section_id: str,
        memory_name: str,
        dry_run: bool = False
    ) -> Dict:
        """
        更新指定章节到记忆文件

        Args:
            docx_path: DOCX 文件路径
            section_id: 章节号，如 "2.1"、"第2章"
            memory_name: 记忆文件名
            dry_run: 是否仅预览不写入

        Returns:
            {
                'status': 'success' | 'cancelled' | 'error',
                'message': str,
                'diff': str,  # Markdown diff
                'backup_path': str,  # 备份路径（如果成功）
                'section_count': int  # 提取的章节数
            }
        """
        try:
            # 1. 检测章节结构
            tree = self.detector.detect(docx_path)

            # 2. 提取指定章节（含子节）
            section_content = self.extractor.extract(tree, section_id)

            if not section_content:
                return {
                    'status': 'error',
                    'message': f'章节 "{section_id}" 不存在'
                }

            # 3. 确定记忆文件路径
            memory_path = self.memory_dir / memory_name

            # 4. 生成 diff
            diff = self.updater.generate_diff(
                memory_path if memory_path.exists() else None,
                section_content,
                section_id
            )

            # 5. 如果是 dry_run，直接返回 diff
            if dry_run:
                return {
                    'status': 'dry_run',
                    'message': '预览模式，未写入',
                    'diff': diff,
                    'section_count': len(section_content)
                }

            # 6. 用户确认（这里返回 diff 供外部确认）
            # 注意：实际确认逻辑在外部处理
            return {
                'status': 'pending_confirm',
                'message': '请审核 diff 后确认写入',
                'diff': diff,
                'section_count': len(section_content),
                'memory_path': str(memory_path)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def confirm_update(
        self,
        memory_path: str,
        section_content: List[Dict],
        section_id: str
    ) -> Dict:
        """
        用户确认后执行更新

        Args:
            memory_path: 记忆文件路径
            section_content: 提取的章节内容
            section_id: 章节号

        Returns:
            {
                'status': 'success' | 'error',
                'message': str,
                'backup_path': str
            }
        """
        try:
            path = Path(memory_path)

            # 1. 创建备份
            backup_path = self._create_backup(path)

            # 2. 原子写入
            self.updater.write_section(path, section_content, section_id)

            return {
                'status': 'success',
                'message': f'章节 {section_id} 更新成功',
                'backup_path': backup_path
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def scan_full(
        self,
        docx_path: str,
        memory_name: str,
        dry_run: bool = False
    ) -> Dict:
        """
        全量扫描 DOCX，重建记忆文件

        Args:
            docx_path: DOCX 文件路径
            memory_name: 记忆文件名
            dry_run: 是否仅预览

        Returns:
            同 update_section
        """
        try:
            # 1. 检测所有章节
            tree = self.detector.detect(docx_path)

            # 2. 提取所有一级章节
            all_sections = []
            for heading in tree.headings:
                if heading.level == 1:
                    section_content = self.extractor.extract(tree, heading.numbering_str)
                    all_sections.extend(section_content)

            # 3. 生成完整记忆内容
            memory_path = self.memory_dir / memory_name

            if dry_run:
                preview = self.updater.generate_full_preview(
                    docx_path,
                    tree,
                    all_sections
                )
                return {
                    'status': 'dry_run',
                    'message': '预览模式，未写入',
                    'preview': preview,
                    'section_count': len(tree.get_level1_sections())
                }

            # 4. 返回待确认状态
            return {
                'status': 'pending_confirm',
                'message': '请审核预览后确认写入',
                'tree': tree,
                'sections': all_sections,
                'memory_path': str(memory_path)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def _create_backup(self, memory_path: Path) -> str:
        """创建记忆文件备份"""
        if not memory_path.exists():
            return None

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = memory_path.parent / f"{memory_path.stem}.backup.{timestamp}.md"

        # 复制原文件
        backup_path.write_bytes(memory_path.read_bytes())

        return str(backup_path)


__version__ = '1.0.0'
__all__ = ['PaperMemoryManager']
