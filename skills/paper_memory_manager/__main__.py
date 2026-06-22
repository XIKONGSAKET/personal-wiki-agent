"""
Paper Memory Manager - CLI Entry Point

命令行接口：
    python -m paper_memory_manager <docx_path> [options]

示例：
    python -m paper_memory_manager "论文.docx" --section "2.1" --memory "论文记忆.md"
    python -m paper_memory_manager "论文.docx" --scan --memory "论文记忆.md"
"""

import argparse
import sys
from pathlib import Path

from . import PaperMemoryManager


def main():
    parser = argparse.ArgumentParser(
        description='论文记忆管理器 - 增量读取 DOCX 章节并同步到记忆文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 更新指定章节
  python -m paper_memory_manager "论文.docx" --section "2.1" --memory "论文记忆.md"

  # 预览模式（不写入）
  python -m paper_memory_manager "论文.docx" --section "2.1" --dry-run

  # 全量扫描
  python -m paper_memory_manager "论文.docx" --scan --memory "论文记忆.md"

  # 指定记忆文件目录
  python -m paper_memory_manager "论文.docx" --section "2.1" --memory-dir "./wiki/meta"
        """
    )

    parser.add_argument('docx', help='DOCX 文件路径')
    parser.add_argument('--section', '-s', help='章节号，如 "2.1"、"第2章"')
    parser.add_argument('--scan', action='store_true', help='全量扫描（记住当前状态）')
    parser.add_argument('--memory', '-m', help='记忆文件名')
    parser.add_argument('--memory-dir', '-d', default='./wiki/meta', help='记忆文件目录（默认: ./wiki/meta）')
    parser.add_argument('--dry-run', '-n', action='store_true', help='预览模式，不写入')
    parser.add_argument('--confirm', action='store_true', help='自动确认（跳过审核）')

    args = parser.parse_args()

    # 验证输入
    if not args.section and not args.scan:
        print("错误: 必须指定 --section 或 --scan", file=sys.stderr)
        sys.exit(1)

    if args.section and args.scan:
        print("错误: --section 和 --scan 不能同时使用", file=sys.stderr)
        sys.exit(1)

    if not args.scan and not args.memory:
        print("错误: 非扫描模式需要指定 --memory", file=sys.stderr)
        sys.exit(1)

    # 检查 DOCX 文件
    docx_path = Path(args.docx)
    if not docx_path.exists():
        print(f"错误: DOCX 文件不存在: {docx_path}", file=sys.stderr)
        sys.exit(1)

    # 初始化管理器
    manager = PaperMemoryManager(memory_dir=args.memory_dir)

    # 执行命令
    try:
        if args.section:
            # 更新指定章节
            result = manager.update_section(
                docx_path=str(docx_path),
                section_id=args.section,
                memory_name=args.memory,
                dry_run=args.dry_run
            )
        else:
            # 全量扫描
            memory_name = args.memory or f"论文记忆-{docx_path.stem}.md"
            result = manager.scan_full(
                docx_path=str(docx_path),
                memory_name=memory_name,
                dry_run=args.dry_run
            )

        # 处理结果
        if result['status'] == 'error':
            print(f"错误: {result['message']}", file=sys.stderr)
            sys.exit(1)

        elif result['status'] == 'dry_run':
            print("=" * 60)
            print("预览模式（未写入）")
            print("=" * 60)
            print()
            if 'diff' in result:
                print(result['diff'])
            elif 'preview' in result:
                print(result['preview'])
            print()
            print(f"提取章节数: {result.get('section_count', 0)}")
            print("使用 --confirm 或在外部确认后再次运行以写入")

        elif result['status'] == 'pending_confirm':
            print("=" * 60)
            print("待确认")
            print("=" * 60)
            print()
            if 'diff' in result:
                print(result['diff'])
            print()
            print(f"提取章节数: {result.get('section_count', 0)}")
            print(f"记忆文件: {result.get('memory_path', 'N/A')}")
            print()

            if args.confirm:
                # 自动确认
                confirm_result = manager.confirm_update(
                    memory_path=result['memory_path'],
                    section_content=result.get('section_content', []),
                    section_id=args.section or 'full'
                )
                if confirm_result['status'] == 'success':
                    print(f"✓ {confirm_result['message']}")
                    if confirm_result.get('backup_path'):
                        print(f"备份: {confirm_result['backup_path']}")
                else:
                    print(f"✗ {confirm_result['message']}", file=sys.stderr)
                    sys.exit(1)
            else:
                print("确认后运行相同命令添加 --confirm 参数以写入")

        elif result['status'] == 'success':
            print(f"✓ {result['message']}")
            if result.get('backup_path'):
                print(f"备份: {result['backup_path']}")

    except KeyboardInterrupt:
        print("\n操作已取消", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
