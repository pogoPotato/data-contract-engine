import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict

class MetricsCharts:
    @staticmethod
    def pass_rate_line(df: pd.DataFrame, title: str = "Pass Rate Trend") -> go.Figure:
        fig = px.line(
            df,
            x='date',
            y='pass_rate',
            title=title,
            labels={'pass_rate': 'Pass Rate (%)', 'date': 'Date'}
        )
        fig.update_traces(line_color='#00CC96', line_width=3)
        fig.update_layout(
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    @staticmethod
    def volume_stacked_bar(df: pd.DataFrame, title: str = "Validation Volume") -> go.Figure:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['passed'],
            name='Passed',
            marker_color='#00CC96',
            hovertemplate='<b>Passed</b>: %{y}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['failed'],
            name='Failed',
            marker_color='#EF553B',
            hovertemplate='<b>Failed</b>: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            barmode='stack',
            title=title,
            xaxis_title='Date',
            yaxis_title='Count',
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    @staticmethod
    def quality_score_area(df: pd.DataFrame, title: str = "Quality Score") -> go.Figure:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['quality_score'],
            fill='tozeroy',
            mode='lines',
            name='Quality Score',
            line=dict(color='#AB63FA', width=3),
            fillcolor='rgba(171, 99, 250, 0.3)',
            hovertemplate='<b>Quality Score</b>: %{y:.1f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Score',
            yaxis_range=[0, 100],
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    @staticmethod
    def error_distribution_bar(error_counts: Dict[str, int], title: str = "Error Distribution") -> go.Figure:
        df = pd.DataFrame([
            {"error_type": k, "count": v}
            for k, v in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        ])
        
        fig = px.bar(
            df,
            x='count',
            y='error_type',
            orientation='h',
            title=title,
            color='count',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(
            xaxis_title='Count',
            yaxis_title='Error Type',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
