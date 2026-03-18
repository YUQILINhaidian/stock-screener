#!/usr/bin/env python3
"""
每日数据更新脚本
自动更新基本面数据、RPS值，并生成最新报告
建议每天收盘后（17:00-18:00）执行
"""

import sys
import os
from datetime import datetime
import logging

# 添加路径
sys.path.insert(0, os.path.expanduser("~"))
sys.path.insert(0, os.path.join(os.path.expanduser("~"), "fundamentals"))

from fundamentals.data_loader import FundamentalDataLoader
from train_daily_strategy import TrainDailyStrategy
from enhanced_rps_viewer import EnhancedRPSViewer


class DailyDataUpdater:
    """每日数据更新器"""
    
    def __init__(self, log_file: str = None):
        """
        初始化更新器
        
        Args:
            log_file: 日志文件路径
        """
        if log_file is None:
            log_file = os.path.expanduser("~/.vntrader/logs/daily_update.log")
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.fundamental_loader = FundamentalDataLoader()
        self.rps_strategy = TrainDailyStrategy()
    
    def update_fundamental_data(self) -> dict:
        """
        更新基本面数据
        
        Returns:
            更新统计信息
        """
        self.logger.info("=" * 60)
        self.logger.info("步骤1: 更新基本面数据")
        self.logger.info("=" * 60)
        
        try:
            # 从VNPy数据库更新价格数据
            stats = self.fundamental_loader.build_from_vnpy_database()
            
            self.logger.info(f"✅ 基本面数据更新完成")
            self.logger.info(f"   成功: {stats['success']} 只")
            self.logger.info(f"   失败: {stats['failed']} 只")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 更新基本面数据失败: {e}")
            return {'success': 0, 'failed': 0, 'error': str(e)}
    
    def update_rps_data(self) -> dict:
        """
        重新计算RPS值
        
        Returns:
            计算统计信息
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("步骤2: 重新计算RPS值")
        self.logger.info("=" * 60)
        
        try:
            # 加载K线数据
            self.logger.info("加载K线数据...")
            self.rps_strategy.load_data()
            
            # 计算RPS
            self.logger.info("计算RPS值（5/10/50/120/250日）...")
            self.rps_strategy.precalculate_all_rps()
            
            self.logger.info("✅ RPS计算完成")
            
            # 统计信息
            stats = {
                'total_stocks': len(self.rps_strategy.all_bars),
                'rps_periods': [5, 10, 50, 120, 250]
            }
            
            self.logger.info(f"   股票数: {stats['total_stocks']}")
            self.logger.info(f"   RPS周期: {stats['rps_periods']}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 更新RPS数据失败: {e}")
            return {'error': str(e)}
    
    def generate_report(self, max_stocks: int = 1000) -> str:
        """
        生成HTML报告
        
        Args:
            max_stocks: 报告中包含的最大股票数
        
        Returns:
            HTML文件路径
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("步骤3: 生成HTML报告")
        self.logger.info("=" * 60)
        
        try:
            viewer = EnhancedRPSViewer()
            
            # 使用已加载的RPS数据
            viewer.rps_strategy = self.rps_strategy
            viewer.fundamental_loader = self.fundamental_loader
            
            # 生成文件名（包含日期）
            output_file = os.path.expanduser(
                f"~/.vntrader/reports/rps_fundamental_report_{datetime.now().strftime('%Y%m%d')}.html"
            )
            
            # 确保目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 生成HTML
            self.logger.info(f"生成报告（包含{max_stocks}只股票）...")
            html_file = viewer.generate_html(output_file=output_file, max_stocks=max_stocks)
            
            self.logger.info(f"✅ 报告生成完成: {html_file}")
            
            return html_file
            
        except Exception as e:
            self.logger.error(f"❌ 生成报告失败: {e}")
            return ""
    
    def run_full_update(self, generate_html: bool = True, max_stocks: int = 1000) -> dict:
        """
        执行完整更新流程
        
        Args:
            generate_html: 是否生成HTML报告
            max_stocks: HTML报告中的股票数量
        
        Returns:
            更新结果统计
        """
        start_time = datetime.now()
        
        self.logger.info("\n" + "🔄" * 30)
        self.logger.info(f"开始每日数据更新 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("🔄" * 30 + "\n")
        
        results = {
            'start_time': start_time.isoformat(),
            'fundamental_stats': {},
            'rps_stats': {},
            'html_file': '',
            'success': False
        }
        
        # 步骤1: 更新基本面数据
        fundamental_stats = self.update_fundamental_data()
        results['fundamental_stats'] = fundamental_stats
        
        if 'error' in fundamental_stats:
            self.logger.error("基本面数据更新失败，中止流程")
            return results
        
        # 步骤2: 更新RPS值
        rps_stats = self.update_rps_data()
        results['rps_stats'] = rps_stats
        
        if 'error' in rps_stats:
            self.logger.error("RPS数据更新失败，中止流程")
            return results
        
        # 步骤3: 生成HTML报告
        if generate_html:
            html_file = self.generate_report(max_stocks=max_stocks)
            results['html_file'] = html_file
        
        # 完成
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results['end_time'] = end_time.isoformat()
        results['duration_seconds'] = duration
        results['success'] = True
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("✅ 每日更新完成")
        self.logger.info("=" * 60)
        self.logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"耗时: {duration:.2f} 秒 ({duration/60:.2f} 分钟)")
        self.logger.info("=" * 60 + "\n")
        
        return results
    
    def cleanup_old_reports(self, keep_days: int = 30):
        """
        清理旧报告
        
        Args:
            keep_days: 保留最近N天的报告
        """
        self.logger.info("\n清理旧报告...")
        
        try:
            from datetime import timedelta
            
            reports_dir = os.path.expanduser("~/.vntrader/reports")
            if not os.path.exists(reports_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            deleted_count = 0
            
            for filename in os.listdir(reports_dir):
                if filename.endswith('.html'):
                    file_path = os.path.join(reports_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
            
            if deleted_count > 0:
                self.logger.info(f"✅ 删除了 {deleted_count} 个旧报告（超过{keep_days}天）")
            else:
                self.logger.info("   没有需要删除的旧报告")
                
        except Exception as e:
            self.logger.error(f"❌ 清理旧报告失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='每日数据更新脚本')
    parser.add_argument('--no-html', action='store_true', help='不生成HTML报告')
    parser.add_argument('--max-stocks', type=int, default=1000, help='HTML报告中的股票数量（默认1000）')
    parser.add_argument('--cleanup', action='store_true', help='清理30天前的旧报告')
    
    args = parser.parse_args()
    
    # 创建更新器
    updater = DailyDataUpdater()
    
    # 执行更新
    results = updater.run_full_update(
        generate_html=not args.no_html,
        max_stocks=args.max_stocks
    )
    
    # 清理旧报告
    if args.cleanup:
        updater.cleanup_old_reports(keep_days=30)
    
    # 返回退出码
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()
