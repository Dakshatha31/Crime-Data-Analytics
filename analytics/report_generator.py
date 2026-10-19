"""
Comprehensive Analytical Report Generator (CSV & PDF).
Satisfies Feature 3: Generate reports filtered by date range, crime category,
district, and year. Include totals, comparisons, and trends with export to CSV and PDF.
Utilizes ReportLab for high-quality PDF document generation.
"""
import sys
import io
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from ingestion.hdfs_manager import hdfs_manager

REPORTS_DIR = PROJECT_ROOT / "reports_out"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ReportGenerator:
    def __init__(self):
        pass

    def filter_data(self,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    crime_category: Optional[str] = None,
                    area_name: Optional[str] = None,
                    year: Optional[int] = None) -> pd.DataFrame:
        """Filter dataset according to selected parameters."""
        cleaned_path = hdfs_manager._resolve_local_path("/crime/processed/cleaned_pig/cleaned_crimes.csv")
        if not cleaned_path.exists():
            cleaned_path = PROJECT_ROOT / "dataset" / "crime_records.csv"

        df = pd.read_csv(cleaned_path)

        if crime_category and crime_category.upper() != "ALL":
            df = df[df["crime_type"].str.upper() == crime_category.upper()]

        if area_name and area_name != "ALL":
            df = df[df["area_name"] == area_name]

        if year and str(year) != "ALL":
            df = df[df["crime_year"] == int(year)]

        if start_date:
            try:
                df = df[df["crime_datetime"] >= start_date]
            except Exception:
                pass

        if end_date:
            try:
                df = df[df["crime_datetime"] <= end_date + " 23:59:59"]
            except Exception:
                pass

        return df

    def generate_report_summary(self,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None,
                                crime_category: Optional[str] = None,
                                area_name: Optional[str] = None,
                                year: Optional[int] = None) -> Dict[str, Any]:
        """Produce tabular summary metrics for the filtered subset."""
        df = self.filter_data(start_date, end_date, crime_category, area_name, year)
        total_crimes = len(df)

        if total_crimes == 0:
            return {
                "status": "warning",
                "total_crimes": 0,
                "message": "No incidents found matching specified criteria."
            }

        # Category totals
        cat_counts = df["crime_type"].value_counts().head(10).to_dict()
        area_counts = df["area_name"].value_counts().head(10).to_dict()
        arrest_count = int(df["arrest_flag"].sum()) if "arrest_flag" in df.columns else 0
        arrest_rate = round((arrest_count / total_crimes) * 100.0, 1)

        # Year and Monthly trends
        monthly_trend = df.groupby(["crime_year", "crime_month"]).size().reset_index(name="count")
        monthly_trend["ym"] = monthly_trend.apply(lambda r: f"{int(r['crime_year'])}-{int(r['crime_month']):02d}", axis=1)
        monthly_series = monthly_trend[["ym", "count"]].to_dict(orient="records")

        return {
            "status": "success",
            "filters_applied": {
                "start_date": start_date or "All History",
                "end_date": end_date or "Present",
                "crime_category": crime_category or "All Categories",
                "area_name": area_name or "All Areas",
                "year": year or "All Years"
            },
            "metrics": {
                "total_incidents": total_crimes,
                "arrests_made": arrest_count,
                "arrest_rate_pct": arrest_rate,
                "distinct_areas": int(df["area_name"].nunique()),
                "distinct_categories": int(df["crime_type"].nunique())
            },
            "top_crime_types": [{"category": k, "count": int(v)} for k, v in cat_counts.items()],
            "top_areas": [{"area": k, "count": int(v)} for k, v in area_counts.items()],
            "monthly_trend": monthly_series,
            "sample_records": df.head(15).to_dict(orient="records")
        }

    def export_csv(self,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   crime_category: Optional[str] = None,
                   area_name: Optional[str] = None,
                   year: Optional[int] = None) -> Path:
        """Export filtered report to CSV file."""
        df = self.filter_data(start_date, end_date, crime_category, area_name, year)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"crime_analytics_report_{timestamp}.csv"
        out_path = REPORTS_DIR / filename
        df.to_csv(out_path, index=False)
        return out_path

    def export_pdf(self,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   crime_category: Optional[str] = None,
                   area_name: Optional[str] = None,
                   year: Optional[int] = None) -> Path:
        """Generate formatted PDF executive report using ReportLab."""
        df = self.filter_data(start_date, end_date, crime_category, area_name, year)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"crime_analytics_report_{timestamp}.pdf"
        out_path = REPORTS_DIR / filename

        doc = SimpleDocTemplate(
            str(out_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#475569")
        )
        h2_style = ParagraphStyle(
            "DocH2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=4
        )
        cell_style = ParagraphStyle(
            "CellNormal",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#334155")
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold"
        )

        elements = []

        # Header Title
        elements.append(Paragraph("CRIME DATA ANALYTICS & INTELLIGENCE REPORT", title_style))
        elements.append(Paragraph(f"Generated on {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')} | Apache Hadoop & Hive Aggregations", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3b82f6"), spaceAfter=12))

        # Filter Parameters Table
        elements.append(Paragraph("1. Report Parameters & Scope", h2_style))
        param_data = [
            [Paragraph("Crime Category", cell_bold), Paragraph(crime_category or "All Categories", cell_style),
             Paragraph("Target Area", cell_bold), Paragraph(area_name or "All Areas", cell_style)],
            [Paragraph("Target Year", cell_bold), Paragraph(str(year) if year else "All Historical Years", cell_style),
             Paragraph("Date Window", cell_bold), Paragraph(f"{start_date or 'Earliest'} to {end_date or 'Latest'}", cell_style)]
        ]
        param_table = Table(param_data, colWidths=[110, 160, 110, 160])
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(param_table)
        elements.append(Spacer(1, 12))

        # Executive Summary Metrics
        total_incidents = len(df)
        arrests = int(df["arrest_flag"].sum()) if "arrest_flag" in df.columns else 0
        arrest_rate = round((arrests / total_incidents) * 100.0, 1) if total_incidents > 0 else 0.0

        elements.append(Paragraph("2. Executive Summary Metrics", h2_style))
        metrics_data = [
            [
                Paragraph("<b>Total Recorded Incidents</b><br/><font size='14' color='#2563eb'><b>" + f"{total_incidents:,}" + "</b></font>", cell_style),
                Paragraph("<b>Total Arrests Made</b><br/><font size='14' color='#059669'><b>" + f"{arrests:,}" + "</b></font>", cell_style),
                Paragraph("<b>Arrest Clearance Rate</b><br/><font size='14' color='#7c3aed'><b>" + f"{arrest_rate}%" + "</b></font>", cell_style),
                Paragraph("<b>Active Districts Covered</b><br/><font size='14' color='#d97706'><b>" + f"{df['area_name'].nunique()}" + "</b></font>", cell_style)
            ]
        ]
        metrics_table = Table(metrics_data, colWidths=[135, 135, 135, 135])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 14))

        # Top Crime Categories Breakdown
        elements.append(Paragraph("3. Incidents by Crime Classification", h2_style))
        cat_counts = df["crime_type"].value_counts().head(8)
        table_cats = [[Paragraph("Crime Classification", cell_bold), Paragraph("Incident Count", cell_bold), Paragraph("% Share", cell_bold)]]
        for c_type, count in cat_counts.items():
            pct = round((count / total_incidents) * 100.0, 1) if total_incidents > 0 else 0
            table_cats.append([Paragraph(str(c_type), cell_style), Paragraph(f"{count:,}", cell_style), Paragraph(f"{pct}%", cell_style)])

        cat_table = Table(table_cats, colWidths=[240, 150, 150])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 14))

        # Top Affected Areas Breakdown
        elements.append(Paragraph("4. Geographic Breakdown (Top Areas)", h2_style))
        area_counts = df["area_name"].value_counts().head(8)
        table_areas = [[Paragraph("Area / Sector Name", cell_bold), Paragraph("Total Crimes Recorded", cell_bold), Paragraph("% of City Total", cell_bold)]]
        for a_name, count in area_counts.items():
            pct = round((count / total_incidents) * 100.0, 1) if total_incidents > 0 else 0
            table_areas.append([Paragraph(str(a_name), cell_style), Paragraph(f"{count:,}", cell_style), Paragraph(f"{pct}%", cell_style)])

        area_table = Table(table_areas, colWidths=[240, 150, 150])
        area_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(area_table)
        elements.append(Spacer(1, 20))

        # Disclaimer Footer
        footer_style = ParagraphStyle(
            "FooterNotice",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b")
        )
        elements.append(Paragraph("<b>Notice:</b> This report was automatically compiled by the Big Data Crime Analytics Platform using HDFS, Pig data normalization, and Hive aggregations. Synthetic data generated for research and demonstration purposes.", footer_style))

        doc.build(elements)
        return out_path


# Global singleton
report_generator = ReportGenerator()

if __name__ == "__main__":
    print("[*] Generating test PDF report...")
    pdf_path = report_generator.export_pdf(crime_category="ALL")
    print(f"[+] Successfully created PDF report: {pdf_path}")
