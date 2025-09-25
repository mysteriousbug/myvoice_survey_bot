import streamlit as st 
import pymongo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import uuid
from datetime import datetime
from collections import Counter

# MongoDB Configuration
@st.cache_resource
def init_connection():
    """Initialize MongoDB connection"""
    try:
        # Get MongoDB URI from environment variable or Streamlit secrets
        mongo_uri = st.secrets.get("MONGODB_URI", "mongodb://localhost:27017/")
        client = pymongo.MongoClient(mongo_uri)
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

@st.cache_data
def get_data():
    """Fetch data from MongoDB"""
    client = init_connection()
    if client is None:
        return pd.DataFrame()
    
    try:
        db = client.employee_survey
        collection = db.responses
        data = list(collection.find({}, {'_id': 0}))
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

# Survey Questions and Options
SURVEY_QUESTIONS = {
    "Q1_Retention_Transformation": {
        "question": "What specific factors related to the Bank's transformation are influencing your decision to stay or consider leaving?",
        "options": {
            "A": "Optimistic about transformation - I see clear benefits from the changes, understand my role in the new structure, and feel confident about career growth opportunities",
            "B": "Cautiously supportive - I support the transformation direction but need more clarity on timeline, my role, and how success will be measured",
            "C": "Concerned but hopeful - I'm worried about job security and increased workload, but believe things will improve with better communication and support",
            "D": "Considering leaving - The uncertainty, lack of clear direction, and impact on work-life balance are making me actively consider other opportunities"
        }
    },
    "Q2_Workload_Stress": {
        "question": "How realistic are your current workloads and deadlines given available resources?",
        "options": {
            "A": "Manageable with current support - Workload is reasonable, deadlines are achievable, and I receive adequate support from my manager",
            "B": "Stretched but coping - Workload is high but manageable with occasional support; need more flexible deadlines during peak periods",
            "C": "Overwhelmed regularly - Consistently struggle to meet deadlines, work long hours frequently, need better resource allocation and prioritization help",
            "D": "Unsustainable pressure - Workload is unrealistic, affecting health and personal life significantly; need immediate intervention and workload redistribution"
        }
    },
    "Q3_Decision_Making": {
        "question": "How would you rate the decision-making processes and communication in your work environment?",
        "options": {
            "A": "Generally effective - Decisions are made in reasonable timeframes with clear communication about rationale and next steps",
            "B": "Occasional delays - Some decisions take longer than needed, but usually get clarity eventually; would benefit from regular updates",
            "C": "Frequent bottlenecks - Often wait weeks for decisions, causing project delays and rework; need clearer escalation processes and timelines",
            "D": "Significantly impacted - Decision delays are causing major disruptions, missed opportunities, and team frustration; need complete process overhaul"
        }
    },
    "Q4_Input_Involvement": {
        "question": "Do you feel your input is genuinely considered when changes affecting your work are being planned?",
        "options": {
            "A": "Actively involved - Regularly consulted on changes, feel my input is valued and see it reflected in final decisions",
            "B": "Sometimes consulted - Asked for input on some changes but not always sure how it's used; would like more feedback on suggestions",
            "C": "Rarely involved - Occasionally asked for input but decisions seem pre-made; need earlier involvement in planning stages",
            "D": "Not consulted - Changes are usually announced without prior consultation; feel like my expertise and experience are undervalued"
        }
    },
    "Q5_Performance_Recognition": {
        "question": "How fairly do you feel your contributions and performance are evaluated compared to your peers?",
        "options": {
            "A": "Fair and transparent - Evaluation process is clear, consistent across the team, and my contributions are appropriately recognized",
            "B": "Generally fair - Mostly satisfied with evaluations but would like more specific feedback and clearer criteria for recognition",
            "C": "Inconsistent treatment - Notice differences in how similar contributions are evaluated; need more standardized and objective criteria",
            "D": "Unfair or biased - Feel my contributions are undervalued compared to peers; evaluation process lacks transparency and consistency"
        }
    },
    "Q6_Personal_Growth": {
        "question": "How effectively is your People Leader supporting your personal growth and career development?",
        "options": {
            "A": "Strong support - Manager actively discusses my development, provides growth opportunities, and helps navigate career path during changes",
            "B": "Basic support - Some development conversations happen but could be more regular and focused; need more specific skill-building opportunities",
            "C": "Limited support - Development discussions are infrequent and surface-level; need more concrete development plans and learning opportunities",
            "D": "No meaningful support - Rarely discuss development, no clear growth path, feel like development has been deprioritized during transformation"
        }
    },
    "Q7_Tools_Resources": {
        "question": "What tools, data, or resources do you need but currently lack adequate access to?",
        "options": {
            "A": "Well-equipped - Have access to all necessary tools and data to perform effectively, with good technical support available",
            "B": "Minor gaps - Most tools are available but some upgrades or additional access would improve efficiency and quality of work",
            "C": "Significant limitations - Missing several important tools or data sources, causing delays and workarounds that reduce productivity",
            "D": "Major impediments - Lack of basic tools/data is seriously hampering ability to do job effectively and deliver quality results"
        }
    },
    "Q8_Follow_up_Accountability": {
        "question": "Of the actions promised from previous My Voice results, how would you rate the follow-through?",
        "options": {
            "A": "Strong follow-through - Most promised actions were delivered effectively, can see clear improvements, and trust the feedback process",
            "B": "Mixed results - Some actions were implemented well while others fell short; generally still believe in the process but expect better execution",
            "C": "Limited progress - Few meaningful changes despite promises; starting to question whether feedback leads to real improvement",
            "D": "Broken promises - Most commitments were not delivered as promised; lost confidence in the survey process and management's commitment to change"
        }
    },
    "Q9_Work_Environment": {
        "question": "What changes to work environment, organizational culture, or team dynamics would have the greatest positive impact?",
        "options": {
            "A": "Environment is positive - Current culture and team dynamics are supportive and conducive to good work; minor tweaks would help",
            "B": "Need collaboration improvements - Good foundation but need better cross-team communication and more collaborative decision-making",
            "C": "Cultural issues - Significant problems with blame culture, politics, or lack of psychological safety that need addressing",
            "D": "Toxic environment - Major cultural problems affecting morale, performance, and well-being; need fundamental culture change"
        }
    },
    "Q10_Open_Communication": {
        "question": "How comfortable do you feel expressing challenging views or concerns?",
        "options": {
            "A": "Very comfortable - Feel safe expressing any concerns or challenging ideas, with leadership actively encouraging diverse viewpoints",
            "B": "Generally comfortable - Usually feel safe speaking up but sometimes hesitate on sensitive topics; would benefit from more encouragement",
            "C": "Selective comfort - Comfortable with some topics/managers but not others; need more consistent psychological safety across the organization",
            "D": "Uncomfortable/afraid - Often afraid to express challenging views due to fear of negative consequences or retaliation"
        }
    },
    "Q11_AI_Future_Readiness": {
        "question": "How excited are you about AI implementation and other technological changes?",
        "options": {
            "A": "Enthusiastic and prepared - Excited about AI opportunities, feel adequately skilled, and confident about adapting to technological changes",
            "B": "Interested but need training - See the potential benefits but need specific training and support to develop necessary skills and confidence",
            "C": "Anxious but willing - Worried about keeping up with changes but willing to learn; need comprehensive training and ongoing support",
            "D": "Fearful of being left behind - Concerned that technological changes will make my skills obsolete; need immediate intensive support and training"
        }
    },
    "Q12_Most_Important_Action": {
        "question": "What single most important action could the Bank take to improve your overall experience?",
        "options": {
            "A": "Improve communication and transparency - Provide clearer, more frequent communication about strategy, changes, and how they affect individuals",
            "B": "Address workload and work-life balance - Implement realistic workload management and support better work-life balance during transformation",
            "C": "Invest in people development - Prioritize employee growth, training, and career development to help navigate the changing landscape",
            "D": "Demonstrate genuine commitment to employee feedback - Take concrete, visible action on employee concerns and consistently follow through on promises"
        }
    }
}

def save_response(response_data):
    """Save survey response to MongoDB"""
    client = init_connection()
    if client is None:
        return False
    
    try:
        db = client.employee_survey
        collection = db.responses
        collection.insert_one(response_data)
        return True
    except Exception as e:
        st.error(f"Failed to save response: {e}")
        return False

def survey_form():
    """Display the survey form"""
    st.header("🎯 2026 My Voice Employee Survey")
    st.write("Your feedback is valuable and will be kept confidential. Please answer all questions honestly.")
    
    with st.form("employee_survey"):
        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        
        st.info(f"📝 Interview Session ID: **{session_id}**")
        
        responses = {}
        
        # Display all questions
        for question_id, question_data in SURVEY_QUESTIONS.items():
            st.subheader(f"Question {question_id.split('_')[0][1:]}")
            st.write(question_data["question"])
            
            # Create selectbox with options
            option_labels = [f"{key}: {value[:100]}..." if len(value) > 100 else f"{key}: {value}" 
                           for key, value in question_data["options"].items()]
            
            selected_option = st.selectbox(
                "Select your response:",
                options=list(question_data["options"].keys()),
                format_func=lambda x: f"{x}: {question_data['options'][x][:100]}..." if len(question_data['options'][x]) > 100 else f"{x}: {question_data['options'][x]}",
                key=question_id
            )
            
            responses[question_id] = selected_option
            st.write("---")
        
        # Submit button
        submitted = st.form_submit_button("📤 Submit Survey", type="primary")
        
        if submitted:
            # Prepare data for saving
            response_data = {
                "session_id": session_id,
                "timestamp": datetime.now(),
                "responses": responses
            }
            
            # Save to MongoDB
            if save_response(response_data):
                st.success(f"✅ Survey submitted successfully! Session ID: {session_id}")
                st.balloons()
                
                # Option to start new survey
                if st.button("🔄 Start New Survey"):
                    st.experimental_rerun()
            else:
                st.error("❌ Failed to submit survey. Please try again.")

def create_response_distribution_chart(df, question_id):
    """Create a pie chart for response distribution"""
    if question_id not in df.columns:
        return None
    
    response_counts = df[question_id].value_counts()
    
    fig = px.pie(
        values=response_counts.values,
        names=response_counts.index,
        title=f"Response Distribution - {question_id.replace('_', ' ').title()}"
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    return fig

def create_overall_sentiment_chart(df):
    """Create overall sentiment analysis chart"""
    # Define positive responses (A and B options generally indicate better sentiment)
    positive_questions = []
    neutral_questions = []
    negative_questions = []
    
    for col in df.columns:
        if col.startswith('Q') and '_' in col:
            positive_count = len(df[df[col].isin(['A', 'B'])])
            negative_count = len(df[df[col].isin(['C', 'D'])])
            
            if positive_count > negative_count:
                positive_questions.append(col)
            elif negative_count > positive_count:
                negative_questions.append(col)
            else:
                neutral_questions.append(col)
    
    sentiment_data = {
        'Sentiment': ['Positive Areas', 'Neutral Areas', 'Areas of Concern'],
        'Count': [len(positive_questions), len(neutral_questions), len(negative_questions)],
        'Color': ['#2E8B57', '#FFD700', '#DC143C']
    }
    
    fig = px.bar(
        sentiment_data,
        x='Sentiment',
        y='Count',
        color='Color',
        title='Overall Survey Sentiment Analysis',
        color_discrete_map={color: color for color in sentiment_data['Color']}
    )
    
    return fig

def analytics_dashboard():
    """Display analytics dashboard"""
    st.header("📊 Survey Analytics Dashboard")
    
    # Load data
    df = get_data()
    
    if df.empty:
        st.warning("⚠️ No survey data available yet. Complete some surveys first!")
        return
    
    # Flatten responses for analysis
    flattened_data = []
    for _, row in df.iterrows():
        flat_row = {
            'session_id': row['session_id'],
            'timestamp': row['timestamp']
        }
        flat_row.update(row['responses'])
        flattened_data.append(flat_row)
    
    analysis_df = pd.DataFrame(flattened_data)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Responses", len(analysis_df))
    
    with col2:
        # Calculate retention concern (Q1 responses C and D indicate concern)
        retention_concern = len(analysis_df[analysis_df['Q1_Retention_Transformation'].isin(['C', 'D'])])
        retention_concern_pct = (retention_concern / len(analysis_df)) * 100 if len(analysis_df) > 0 else 0
        st.metric("Retention Concern", f"{retention_concern_pct:.1f}%")
    
    with col3:
        # Calculate stress level (Q2 responses C and D indicate high stress)
        high_stress = len(analysis_df[analysis_df['Q2_Workload_Stress'].isin(['C', 'D'])])
        high_stress_pct = (high_stress / len(analysis_df)) * 100 if len(analysis_df) > 0 else 0
        st.metric("High Stress Level", f"{high_stress_pct:.1f}%")
    
    with col4:
        # Calculate satisfaction (average of A responses across all questions)
        total_responses = len(analysis_df) * 12 # 12 questions
        a_responses = sum([len(analysis_df[analysis_df[col] == 'A']) for col in analysis_df.columns if col.startswith('Q')])
        satisfaction_pct = (a_responses / total_responses) * 100 if total_responses > 0 else 0
        st.metric("Overall Satisfaction", f"{satisfaction_pct:.1f}%")
    
    st.write("---")
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Question Analysis", "🎯 Priority Areas", "📅 Trends", "📋 Raw Data"])
    
    with tab1:
        st.subheader("Individual Question Analysis")
        
        # Question selector
        question_options = [col for col in analysis_df.columns if col.startswith('Q')]
        selected_question = st.selectbox("Select Question to Analyze:", question_options)
        
        if selected_question:
            # Create pie chart
            fig = create_response_distribution_chart(analysis_df, selected_question)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Show detailed breakdown
            st.subheader("Response Breakdown")
            response_counts = analysis_df[selected_question].value_counts()
            question_data = SURVEY_QUESTIONS[selected_question]
            
            for option, count in response_counts.items():
                percentage = (count / len(analysis_df)) * 100
                st.write(f"**Option {option}** ({percentage:.1f}%): {question_data['options'][option]}")
    
    with tab2:
        st.subheader("Priority Areas for Action")
        
        # Calculate concern levels for each question
        concern_scores = {}
        for col in analysis_df.columns:
            if col.startswith('Q'):
                # Count C and D responses as concerns
                concern_count = len(analysis_df[analysis_df[col].isin(['C', 'D'])])
                concern_scores[col] = (concern_count / len(analysis_df)) * 100
        
        # Sort by concern level
        sorted_concerns = sorted(concern_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Create bar chart
        concern_df = pd.DataFrame(sorted_concerns, columns=['Question', 'Concern_Level'])
        fig = px.bar(
            concern_df,
            x='Concern_Level',
            y='Question',
            orientation='h',
            title='Areas Requiring Immediate Attention (% of Concerning Responses)',
            labels={'Concern_Level': 'Concern Level (%)', 'Question': 'Survey Questions'}
        )
        fig.update_traces(marker_color='lightcoral')
        st.plotly_chart(fig, use_container_width=True)
        
        # Show top concerns
        st.subheader("Top 5 Areas of Concern")
        for i, (question, score) in enumerate(sorted_concerns[:5], 1):
            question_title = SURVEY_QUESTIONS[question]["question"][:100] + "..."
            st.write(f"{i}. **{question}** ({score:.1f}% concern): {question_title}")
    
    with tab3:
        st.subheader("Response Trends Over Time")
        
        if 'timestamp' in analysis_df.columns:
            # Convert timestamp to date
            analysis_df['date'] = pd.to_datetime(analysis_df['timestamp']).dt.date
            
            # Responses over time
            daily_responses = analysis_df.groupby('date').size()
            
            fig = px.line(
                x=daily_responses.index,
                y=daily_responses.values,
                title='Survey Responses Over Time',
                labels={'x': 'Date', 'y': 'Number of Responses'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Timestamp data not available for trend analysis.")
    
    with tab4:
        st.subheader("Raw Survey Data")
        
        # Display filters
        col1, col2 = st.columns(2)
        
        with col1:
            if 'timestamp' in analysis_df.columns:
                date_range = st.date_input(
                    "Filter by Date Range",
                    value=(analysis_df['timestamp'].min().date(), analysis_df['timestamp'].max().date())
                )
        
        with col2:
            session_filter = st.multiselect(
                "Filter by Session ID",
                options=analysis_df['session_id'].unique(),
                default=analysis_df['session_id'].unique()
            )
        
        # Apply filters
        filtered_df = analysis_df[analysis_df['session_id'].isin(session_filter)]
        
        # Display data
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download option
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"survey_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def main():
    """Main application"""
    st.set_page_config(
        page_title="Employee Survey System",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar navigation
    st.sidebar.title("🏦 My Voice Survey 2026")
    st.sidebar.write("Navigate through the application:")
    
    page = st.sidebar.radio(
        "Choose a section:",
        ["📝 New Survey", "📊 Analytics", "ℹ️ About"]
    )
    
    if page == "📝 New Survey":
        survey_form()
    
    elif page == "📊 Analytics":
        analytics_dashboard()
    
    elif page == "ℹ️ About":
        st.header("About This Survey System")
        st.write("""
        This application is designed to collect and analyze employee feedback through the annual My Voice survey.
        
        **Features:**
        - ✅ Secure data collection with unique session IDs
        - 📊 Real-time analytics and visualizations
        - 🔍 Detailed response analysis
        - 📈 Trend tracking over time
        - 📥 Data export capabilities
        
        **How to Use:**
        1. **New Survey**: Click 'Start New Interview Session' to begin
        2. **Analytics**: View comprehensive analysis of collected responses
        3. **Export**: Download data for further analysis
        
        **Privacy & Security:**
        - All responses are anonymous
        - Data is securely stored in MongoDB
        - Session IDs are randomly generated
        """)
        
        st.info("💡 **Tip**: Use the Analytics section to identify areas requiring immediate attention based on survey responses.")

if __name__ == "__main__":
    main()
