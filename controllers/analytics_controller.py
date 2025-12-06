"""
KALASAG - Analytics Controller
Business logic for Intelligence & Analytics module.
Implements FR-4.1, FR-4.2, FR-4.3
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from models.analytics import AnalyticsModel

# Import matplotlib for chart generation
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Import pandas for data processing
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class AnalyticsController:
    """Controller for analytics and BI operations."""
    
    # Default output directory for charts
    DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    
    # Chart styling
    CHART_COLORS = {
        'safe': '#28a745',
        'caution': '#ffc107', 
        'hotspot': '#dc3545',
        'primary': '#007bff',
        'secondary': '#6c757d'
    }
    
    @staticmethod
    def get_crime_heatmap_data(days_back: int = 30) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get crime heatmap data for visualization (FR-4.1).
        
        Returns:
            Tuple of (success, message, data)
        """
        try:
            data = AnalyticsModel.get_incident_count_by_purok(days_back=days_back)
            
            if not data:
                return True, "No purok data available", []
            
            return True, f"Retrieved heatmap data for {len(data)} puroks", data
            
        except Exception as e:
            return False, f"Error retrieving heatmap data: {str(e)}", None
    
    @staticmethod
    def get_heatmap_figure(days_back: int = 30, chart_type: str = 'bar') -> Optional[Any]:
        """
        Generate crime heatmap figure for embedding (FR-4.1).
        
        Returns:
            Matplotlib Figure object or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            data = AnalyticsModel.get_incident_count_by_purok(days_back=days_back)
            
            if not data:
                return None
            
            # Use Pandas if available for data processing
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(data)
                puroks = df['purok_name'].tolist()
                counts = df['incident_count'].tolist()
                colors = df['severity_color'].tolist()
            else:
                puroks = [d['purok_name'] for d in data]
                counts = [d['incident_count'] for d in data]
                colors = [d['severity_color'] for d in data]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(6, 4))
            
            if chart_type == 'bar':
                bars = ax.bar(puroks, counts, color=colors, edgecolor='black', linewidth=0.5)
                
                ax.set_xlabel('Purok', fontsize=10)
                ax.set_ylabel('Incident Count', fontsize=10)
                ax.set_title(f'Crime Heatmap (Last {days_back} Days)', fontsize=12, fontweight='bold')
                
                # Rotate labels if many puroks
                if len(puroks) > 5:
                    plt.xticks(rotation=45, ha='right', fontsize=8)
                else:
                    plt.xticks(fontsize=9)
                
                plt.yticks(fontsize=9)
                
                # Add value labels on bars
                for bar, count in zip(bars, counts):
                    if count > 0:
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                               str(count), ha='center', va='bottom', fontsize=8)
                
            else:  # pie chart
                # Filter out zero counts for pie
                pie_data = [(d['purok_name'], d['incident_count'], d['severity_color']) 
                           for d in data if d['incident_count'] > 0]
                
                if not pie_data:
                    ax.text(0.5, 0.5, 'No Incidents Recorded', ha='center', va='center',
                           fontsize=12, transform=ax.transAxes)
                else:
                    labels = [d[0] for d in pie_data]
                    sizes = [d[1] for d in pie_data]
                    colors = [d[2] for d in pie_data]
                    
                    wedges, texts, autotexts = ax.pie(
                        sizes, labels=labels, colors=colors,
                        autopct='%1.1f%%', startangle=90,
                        explode=[0.02] * len(sizes),
                        textprops={'fontsize': 9}
                    )
                    
                    ax.set_title(f'Crime Distribution (Last {days_back} Days)', 
                                fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Error generating heatmap figure: {e}")
            return None

    @staticmethod
    def generate_heatmap_chart(
        days_back: int = 30,
        output_path: str = None,
        chart_type: str = 'bar'
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate crime heatmap chart image (FR-4.1).
        
        Args:
            days_back: Number of days to analyze
            output_path: Path to save chart image
            chart_type: 'bar' or 'pie'
            
        Returns:
            Tuple of (success, message, file_path)
        """
        if not MATPLOTLIB_AVAILABLE:
            return False, "Matplotlib not available for chart generation", None
        
        try:
            data = AnalyticsModel.get_incident_count_by_purok(days_back=days_back)
            
            if not data:
                return False, "No data available for chart", None
            
            # Set up output path
            if not output_path:
                os.makedirs(AnalyticsController.DEFAULT_OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    AnalyticsController.DEFAULT_OUTPUT_DIR,
                    f"heatmap_{chart_type}_{timestamp}.png"
                )
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == 'bar':
                # Bar chart
                puroks = [d['purok_name'] for d in data]
                counts = [d['incident_count'] for d in data]
                colors = [d['severity_color'] for d in data]
                
                bars = ax.bar(puroks, counts, color=colors, edgecolor='black', linewidth=0.5)
                
                ax.set_xlabel('Purok', fontsize=12)
                ax.set_ylabel('Incident Count', fontsize=12)
                ax.set_title(f'Crime Heatmap by Purok (Last {days_back} Days)', fontsize=14, fontweight='bold')
                
                # Rotate labels if many puroks
                if len(puroks) > 5:
                    plt.xticks(rotation=45, ha='right')
                
                # Add value labels on bars
                for bar, count in zip(bars, counts):
                    if count > 0:
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                               str(count), ha='center', va='bottom', fontsize=10)
                
            else:  # pie chart
                # Filter out zero counts for pie
                pie_data = [(d['purok_name'], d['incident_count'], d['severity_color']) 
                           for d in data if d['incident_count'] > 0]
                
                if not pie_data:
                    ax.text(0.5, 0.5, 'No Incidents Recorded', ha='center', va='center',
                           fontsize=14, transform=ax.transAxes)
                else:
                    labels = [d[0] for d in pie_data]
                    sizes = [d[1] for d in pie_data]
                    colors = [d[2] for d in pie_data]
                    
                    wedges, texts, autotexts = ax.pie(
                        sizes, labels=labels, colors=colors,
                        autopct='%1.1f%%', startangle=90,
                        explode=[0.02] * len(sizes)
                    )
                    
                    ax.set_title(f'Crime Distribution by Purok (Last {days_back} Days)', 
                                fontsize=14, fontweight='bold')
            
            # Add legend
            legend_patches = [
                mpatches.Patch(color=AnalyticsController.CHART_COLORS['safe'], label='Safe (0)'),
                mpatches.Patch(color=AnalyticsController.CHART_COLORS['caution'], label='Caution (1-3)'),
                mpatches.Patch(color=AnalyticsController.CHART_COLORS['hotspot'], label='Hotspot (>3)')
            ]
            ax.legend(handles=legend_patches, loc='upper right')
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True, f"Chart saved to {output_path}", output_path
            
        except Exception as e:
            return False, f"Error generating chart: {str(e)}", None
    
    @staticmethod
    def get_time_analysis_data(days_back: int = 30) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get time-series analysis data (FR-4.2).
        
        Returns:
            Tuple with hourly data, daily data, and dangerous periods
        """
        try:
            hourly_data = AnalyticsModel.get_incidents_by_time_of_day(days_back=days_back)
            daily_data = AnalyticsModel.get_incidents_by_day_of_week(days_back=days_back)
            dangerous_hours = AnalyticsModel.get_most_dangerous_hours(days_back=days_back, top_n=3)
            
            # Determine most dangerous day
            most_dangerous_day = max(daily_data, key=lambda x: x['incident_count'])
            
            result = {
                'hourly_distribution': hourly_data,
                'daily_distribution': daily_data,
                'most_dangerous_hours': dangerous_hours,
                'most_dangerous_day': most_dangerous_day,
                'period_summary': AnalyticsController._summarize_by_period(hourly_data)
            }
            
            return True, "Time analysis data retrieved successfully", result
            
        except Exception as e:
            return False, f"Error retrieving time analysis data: {str(e)}", None
    
    @staticmethod
    def _summarize_by_period(hourly_data: List[Dict]) -> Dict[str, int]:
        """Summarize incidents by time period."""
        periods = {'Morning': 0, 'Afternoon': 0, 'Evening': 0, 'Night': 0}
        
        for hour_data in hourly_data:
            period = hour_data['period']
            periods[period] += hour_data['incident_count']
        
        return periods
    
    @staticmethod
    def get_time_analysis_figure(days_back: int = 30) -> Optional[Any]:
        """
        Generate time-series analysis figure for embedding (FR-4.2).
        
        Returns:
            Matplotlib Figure object or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            hourly_data = AnalyticsModel.get_incidents_by_time_of_day(days_back=days_back)
            
            # Use Pandas if available
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(hourly_data)
                hours = df['hour'].tolist()
                counts = df['incident_count'].tolist()
            else:
                hours = [d['hour'] for d in hourly_data]
                counts = [d['incident_count'] for d in hourly_data]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(6, 4))
            
            # Hourly distribution (line chart)
            
            ax.plot(hours, counts, color=AnalyticsController.CHART_COLORS['primary'], 
                    linewidth=2, marker='o', markersize=4)
            ax.fill_between(hours, counts, alpha=0.3, color=AnalyticsController.CHART_COLORS['primary'])
            
            ax.set_xlabel('Hour of Day', fontsize=10)
            ax.set_ylabel('Incident Count', fontsize=10)
            ax.set_title('Incidents by Hour of Day', fontsize=12, fontweight='bold')
            ax.set_xticks(range(0, 24, 4))
            ax.set_xticklabels(['12AM', '4AM', '8AM', '12PM', '4PM', '8PM'], fontsize=9)
            plt.yticks(fontsize=9)
            ax.grid(True, alpha=0.3)
            
            # Highlight peak hours
            if counts:
                max_count = max(counts)
                peak_hours = [h for h, c in zip(hours, counts) if c == max_count and max_count > 0]
                for peak in peak_hours:
                    ax.axvline(x=peak, color=AnalyticsController.CHART_COLORS['hotspot'], 
                               linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Error generating time analysis figure: {e}")
            return None

    @staticmethod
    def generate_time_chart(
        days_back: int = 30,
        output_path: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate time-series analysis chart (FR-4.2).
        
        Returns:
            Tuple of (success, message, file_path)
        """
        if not MATPLOTLIB_AVAILABLE:
            return False, "Matplotlib not available for chart generation", None
        
        try:
            hourly_data = AnalyticsModel.get_incidents_by_time_of_day(days_back=days_back)
            
            # Set up output path
            if not output_path:
                os.makedirs(AnalyticsController.DEFAULT_OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    AnalyticsController.DEFAULT_OUTPUT_DIR,
                    f"time_analysis_{timestamp}.png"
                )
            
            # Create figure with 2 subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            
            # Left: Hourly distribution (line chart)
            hours = [d['hour'] for d in hourly_data]
            counts = [d['incident_count'] for d in hourly_data]
            
            ax1.plot(hours, counts, color=AnalyticsController.CHART_COLORS['primary'], 
                    linewidth=2, marker='o', markersize=4)
            ax1.fill_between(hours, counts, alpha=0.3, color=AnalyticsController.CHART_COLORS['primary'])
            
            ax1.set_xlabel('Hour of Day', fontsize=12)
            ax1.set_ylabel('Incident Count', fontsize=12)
            ax1.set_title('Incidents by Hour of Day', fontsize=14, fontweight='bold')
            ax1.set_xticks(range(0, 24, 3))
            ax1.set_xticklabels(['12AM', '3AM', '6AM', '9AM', '12PM', '3PM', '6PM', '9PM'])
            ax1.grid(True, alpha=0.3)
            
            # Highlight peak hours
            max_count = max(counts)
            peak_hours = [h for h, c in zip(hours, counts) if c == max_count and max_count > 0]
            for peak in peak_hours:
                ax1.axvline(x=peak, color=AnalyticsController.CHART_COLORS['hotspot'], 
                           linestyle='--', alpha=0.7, label=f'Peak: {peak}:00')
            
            # Right: Period distribution (bar chart)
            period_summary = AnalyticsController._summarize_by_period(hourly_data)
            periods = list(period_summary.keys())
            period_counts = list(period_summary.values())
            
            period_colors = [
                AnalyticsController.CHART_COLORS['safe'],      # Morning
                AnalyticsController.CHART_COLORS['caution'],   # Afternoon
                AnalyticsController.CHART_COLORS['hotspot'],   # Evening
                AnalyticsController.CHART_COLORS['secondary']  # Night
            ]
            
            bars = ax2.bar(periods, period_counts, color=period_colors, edgecolor='black', linewidth=0.5)
            ax2.set_xlabel('Time Period', fontsize=12)
            ax2.set_ylabel('Incident Count', fontsize=12)
            ax2.set_title('Incidents by Time Period', fontsize=14, fontweight='bold')
            
            # Add value labels
            for bar, count in zip(bars, period_counts):
                if count > 0:
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                            str(count), ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.suptitle(f'Time-Series Crime Analysis (Last {days_back} Days)', 
                        fontsize=16, fontweight='bold', y=1.02)
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True, f"Chart saved to {output_path}", output_path
            
        except Exception as e:
            return False, f"Error generating chart: {str(e)}", None
    
    @staticmethod
    def get_patrol_recommendations(days_back: int = 30) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get patrol deployment recommendations (FR-4.3).
        
        Returns:
            Tuple of (success, message, recommendations)
        """
        try:
            recommendations = AnalyticsModel.generate_patrol_recommendations(days_back=days_back)
            
            return True, f"Generated {len(recommendations)} patrol recommendations", recommendations
            
        except Exception as e:
            return False, f"Error generating recommendations: {str(e)}", None
    
    @staticmethod
    def format_patrol_report(recommendations: List[Dict]) -> str:
        """
        Format patrol recommendations as a readable text report.
        
        Returns:
            Formatted string report
        """
        if not recommendations:
            return "No patrol recommendations available."
        
        lines = []
        lines.append("=" * 60)
        lines.append("KALASAG - PATROL DEPLOYMENT RECOMMENDATIONS")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)
        lines.append("")
        
        for rec in recommendations:
            severity_icon = {
                'safe': '🟢',
                'caution': '🟡', 
                'hotspot': '🔴'
            }.get(rec['severity_level'], '⚪')
            
            lines.append(f"Priority #{rec['priority']}: {severity_icon}")
            lines.append(f"  Location: {rec['purok_name']}")
            lines.append(f"  Time: {rec['time_range']}")
            lines.append(f"  Reason: {rec['reason']}")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("Deploy patrols according to priority level.")
        lines.append("Red (Hotspot) areas require immediate attention.")
        
        return "\n".join(lines)
    
    @staticmethod
    def get_dashboard_data(days_back: int = 30) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get comprehensive dashboard data for main analytics view.
        
        Returns:
            Tuple of (success, message, dashboard_data)
        """
        try:
            summary = AnalyticsModel.get_dashboard_summary(days_back=days_back)
            purok_data = AnalyticsModel.get_incident_count_by_purok(days_back=days_back)
            type_data = AnalyticsModel.get_incidents_by_type(days_back=days_back)
            monthly_trend = AnalyticsModel.get_monthly_trend(months_back=6)
            recommendations = AnalyticsModel.generate_patrol_recommendations(days_back=days_back)
            
            dashboard = {
                'summary': summary,
                'purok_heatmap': purok_data,
                'incident_types': type_data,
                'monthly_trend': monthly_trend,
                'patrol_recommendations': recommendations[:3],  # Top 3
                'generated_at': datetime.now().isoformat()
            }
            
            return True, "Dashboard data retrieved successfully", dashboard
            
        except Exception as e:
            return False, f"Error retrieving dashboard data: {str(e)}", None
    
    @staticmethod
    def export_analytics_report(
        days_back: int = 30,
        output_path: str = None,
        include_charts: bool = True
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Export comprehensive analytics report.
        
        Returns:
            Tuple of (success, message, report_path)
        """
        try:
            # Get all data
            success, msg, dashboard = AnalyticsController.get_dashboard_data(days_back)
            if not success:
                return False, msg, None
            
            # Set up output path
            if not output_path:
                os.makedirs(AnalyticsController.DEFAULT_OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    AnalyticsController.DEFAULT_OUTPUT_DIR,
                    f"analytics_report_{timestamp}.txt"
                )
            
            # Generate report
            lines = []
            lines.append("=" * 70)
            lines.append("KALASAG - CRIME ANALYTICS REPORT")
            lines.append(f"Report Period: {dashboard['summary']['start_date']} to {dashboard['summary']['end_date']}")
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("=" * 70)
            lines.append("")
            
            # Summary section
            lines.append("EXECUTIVE SUMMARY")
            lines.append("-" * 40)
            lines.append(f"Total Incidents: {dashboard['summary']['total_incidents']}")
            lines.append(f"Pending Cases: {dashboard['summary']['pending_cases']}")
            lines.append(f"Active Residents: {dashboard['summary']['total_residents']}")
            lines.append(f"Hotspot Areas: {dashboard['summary']['hotspot_count']}")
            lines.append(f"Caution Areas: {dashboard['summary']['caution_count']}")
            lines.append(f"Safe Areas: {dashboard['summary']['safe_count']}")
            lines.append("")
            
            # Purok breakdown
            lines.append("AREA BREAKDOWN (by incident count)")
            lines.append("-" * 40)
            for purok in dashboard['purok_heatmap']:
                status = purok['severity_level'].upper()
                lines.append(f"  {purok['purok_name']}: {purok['incident_count']} incidents [{status}]")
            lines.append("")
            
            # Patrol recommendations
            lines.append("PATROL RECOMMENDATIONS")
            lines.append("-" * 40)
            lines.append(AnalyticsController.format_patrol_report(dashboard['patrol_recommendations']))
            
            # Write report
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            
            # Generate charts if requested
            chart_paths = []
            if include_charts and MATPLOTLIB_AVAILABLE:
                base_path = os.path.splitext(output_path)[0]
                
                success, _, heatmap_path = AnalyticsController.generate_heatmap_chart(
                    days_back=days_back,
                    output_path=f"{base_path}_heatmap.png"
                )
                if success:
                    chart_paths.append(heatmap_path)
                
                success, _, time_path = AnalyticsController.generate_time_chart(
                    days_back=days_back,
                    output_path=f"{base_path}_time.png"
                )
                if success:
                    chart_paths.append(time_path)
            
            chart_msg = f" with {len(chart_paths)} charts" if chart_paths else ""
            return True, f"Report saved to {output_path}{chart_msg}", output_path
            
        except Exception as e:
            return False, f"Error exporting report: {str(e)}", None
    
    @staticmethod
    def get_crime_statistics(days_back: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive crime statistics.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict with by_type, by_location, and monthly_trend data
        """
        return {
            'by_type': AnalyticsModel.get_incident_count_by_type(days_back=days_back),
            'by_location': AnalyticsModel.get_incident_count_by_location(days_back=days_back),
            'monthly_trend': AnalyticsModel.get_monthly_trend(months_back=6)
        }
    
    @staticmethod
    def get_demographic_figure(category: str) -> Optional[Any]:
        """
        Generate demographic figure for embedding.
        
        Args:
            category: 'gender', 'civil_status', or 'purok'
            
        Returns:
            Matplotlib Figure object or None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            data = []
            title = ""
            
            if category == 'gender':
                data = AnalyticsModel.get_demographic_by_gender()
                title = "Population by Gender"
                label_key = 'gender'
            elif category == 'civil_status':
                data = AnalyticsModel.get_demographic_by_civil_status()
                title = "Population by Civil Status"
                label_key = 'civil_status'
            elif category == 'purok':
                data = AnalyticsModel.get_demographic_by_purok()
                title = "Population by Purok"
                label_key = 'purok_name'
            else:
                return None
            
            if not data:
                return None
            
            # Create figure
            fig, ax = plt.subplots(figsize=(6, 4))
            
            labels = [d.get(label_key, 'Unknown') for d in data]
            counts = [d.get('count', 0) for d in data]
            
            if category == 'purok':
                # Bar chart for purok (too many for pie)
                bars = ax.bar(labels, counts, color=AnalyticsController.CHART_COLORS['primary'])
                ax.set_title(title, fontsize=12, fontweight='bold')
                plt.xticks(rotation=45, ha='right', fontsize=8)
                
                # Add value labels
                for bar, count in zip(bars, counts):
                    if count > 0:
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                               str(count), ha='center', va='bottom', fontsize=8)
            else:
                # Pie chart for others
                wedges, texts, autotexts = ax.pie(
                    counts, labels=labels, autopct='%1.1f%%', startangle=90,
                    textprops={'fontsize': 9}
                )
                ax.set_title(title, fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Error generating demographic figure: {e}")
            return None

    @staticmethod
    def get_demographic_statistics() -> Dict[str, Any]:
        """
        Get comprehensive demographic statistics.
        
        Returns:
            Dict with by_gender, by_civil_status, by_purok, and by_age_group data
        """
        return {
            'by_gender': AnalyticsModel.get_demographic_by_gender(),
            'by_civil_status': AnalyticsModel.get_demographic_by_civil_status(),
            'by_purok': AnalyticsModel.get_demographic_by_purok(),
            'by_age_group': AnalyticsModel.get_demographic_by_age_group(),
            'voter_stats': AnalyticsModel.get_voter_statistics()
        }
