"""
Service for exporting VPN usage analytics in various formats.
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import logging

logger = logging.getLogger(__name__)

class ExportService:
    """Service for exporting VPN usage analytics."""
    
    def __init__(self):
        """Initialize the export service."""
        self.export_dir = "exports"
        os.makedirs(self.export_dir, exist_ok=True)
        
    async def generate_pdf_report(
        self,
        user_id: int,
        usage: Dict[str, Any],
        stats: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a PDF report of VPN usage.
        
        Args:
            user_id: User ID
            usage: Usage details
            stats: Usage statistics
            history: Usage history
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Create PDF file path
            file_path = os.path.join(
                self.export_dir,
                f"vpn_usage_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            elements.append(Paragraph("گزارش مصرف VPN", title_style))
            
            # Add usage details
            usage_data = [
                ["جزئیات مصرف", ""],
                ["تاریخ شروع", usage['start_date']],
                ["مصرف امروز", f"{usage['daily_usage']:.2f}GB"],
                ["مصرف کل", f"{usage['total_usage']:.2f}GB"],
                ["آخرین بروزرسانی", usage['last_update']],
                ["محدودیت ترافیک", f"{usage['traffic_limit']:.2f}GB"],
                ["روزهای باقیمانده", str(usage['remaining_days'])]
            ]
            
            usage_table = Table(usage_data, colWidths=[2*inch, 2*inch])
            usage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(usage_table)
            elements.append(Spacer(1, 20))
            
            # Add statistics
            stats_data = [
                ["آمار کلی", ""],
                ["زمان کل استفاده", f"{stats['total_duration']:.1f} ساعت"],
                ["میانگین هر جلسه", f"{stats['average_session']:.1f} دقیقه"],
                ["پرکاربردترین سرور", stats['most_used_server']],
                ["مصرف در سرور اصلی", f"{stats['server_usage']:.2f}GB"]
            ]
            
            stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Add history
            history_data = [["تاریخ", "مصرف (GB)", "مدت زمان (ساعت)", "سرور"]]
            for record in history:
                history_data.append([
                    record['date'],
                    f"{record['usage']:.2f}",
                    f"{record['duration']:.1f}",
                    record['server']
                ])
            
            history_table = Table(history_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
            history_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(history_table)
            
            # Build PDF
            doc.build(elements)
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
            
    async def generate_usage_chart(
        self,
        user_id: int,
        history: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a usage chart as an image.
        
        Args:
            user_id: User ID
            history: Usage history
            
        Returns:
            Path to the generated chart image
        """
        try:
            # Create chart file path
            file_path = os.path.join(
                self.export_dir,
                f"vpn_usage_chart_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            
            # Prepare data
            dates = [record['date'] for record in history]
            usage = [record['usage'] for record in history]
            
            # Create chart
            plt.figure(figsize=(10, 6))
            plt.plot(dates, usage, marker='o', linewidth=2, markersize=8)
            plt.title('مصرف VPN در 30 روز گذشته', fontsize=14)
            plt.xlabel('تاریخ', fontsize=12)
            plt.ylabel('مصرف (GB)', fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            
            # Save chart
            plt.tight_layout()
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating usage chart: {str(e)}")
            raise
            
    async def generate_text_report(
        self,
        usage: Dict[str, Any],
        stats: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a text report of VPN usage.
        
        Args:
            usage: Usage details
            stats: Usage statistics
            history: Usage history
            
        Returns:
            Formatted text report
        """
        try:
            report = (
                f"📊 *گزارش مصرف VPN*\n\n"
                f"*جزئیات مصرف:*\n"
                f"• تاریخ شروع: {usage['start_date']}\n"
                f"• مصرف امروز: {usage['daily_usage']:.2f}GB\n"
                f"• مصرف کل: {usage['total_usage']:.2f}GB\n"
                f"• آخرین بروزرسانی: {usage['last_update']}\n"
                f"• محدودیت ترافیک: {usage['traffic_limit']:.2f}GB\n"
                f"• روزهای باقیمانده: {usage['remaining_days']}\n\n"
                f"*آمار کلی:*\n"
                f"• زمان کل استفاده: {stats['total_duration']:.1f} ساعت\n"
                f"• میانگین هر جلسه: {stats['average_session']:.1f} دقیقه\n"
                f"• پرکاربردترین سرور: {stats['most_used_server']}\n"
                f"• مصرف در سرور اصلی: {stats['server_usage']:.2f}GB\n\n"
                f"*تاریخچه مصرف:*\n"
            )
            
            for record in history:
                report += (
                    f"• {record['date']}:\n"
                    f"  - مصرف: {record['usage']:.2f}GB\n"
                    f"  - مدت زمان: {record['duration']:.1f} ساعت\n"
                    f"  - سرور: {record['server']}\n\n"
                )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating text report: {str(e)}")
            raise
            
    async def generate_csv_report(
        self,
        user_id: int,
        history: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a CSV report of VPN usage.
        
        Args:
            user_id: User ID
            history: Usage history
            
        Returns:
            Path to the generated CSV file
        """
        try:
            # Create CSV file path
            file_path = os.path.join(
                self.export_dir,
                f"vpn_usage_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            # Write CSV file
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['تاریخ', 'مصرف (GB)', 'مدت زمان (ساعت)', 'سرور'])
                
                for record in history:
                    writer.writerow([
                        record['date'],
                        f"{record['usage']:.2f}",
                        f"{record['duration']:.1f}",
                        record['server']
                    ])
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating CSV report: {str(e)}")
            raise 