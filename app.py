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
        mongo_uri = st.secrets["MONGODB_URI"]
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
        "question": "How are you feeling about all these changes happening at the bank? Are they making you want to stay or think about leaving?",
        "options": {
            "A": "Pretty excited about it! The changes make sense, I know where I fit, and I can see some good opportunities coming my way",
            "B": "Cautiously optimistic - I get the direction we're going, but I'd love more clarity on timelines and what exactly my role will look like",
            "C": "A bit worried but still hopeful - Concerned about job security and the extra workload, but I think it'll work out if we get better communication",
            "D": "Honestly considering other options - The uncertainty and impact on my work-life balance is really making me think about looking elsewhere"
        }
    },
    "Q2_Workload_Stress": {
        "question": "Let's talk about your workload - are you managing okay with everything on your plate right now?",
        "options": {
            "A": "It's all good! My workload feels reasonable, deadlines are doable, and my manager has my back",
            "B": "It's pretty intense but I'm handling it - could use some flexibility on deadlines when things get crazy busy though",
            "C": "I'm struggling to keep up - working long hours regularly, missing deadlines, and could really use some help with prioritizing",
            "D": "It's honestly unsustainable - the pressure is affecting my health and personal life, something needs to change ASAP"
        }
    },
    "Q3_Decision_Making": {
        "question": "How's the decision-making around here? Do things move at a reasonable pace or are you stuck waiting for answers a lot?",
        "options": {
            "A": "Pretty smooth actually - decisions happen in reasonable time and we usually understand the 'why' behind them",
            "B": "Sometimes we wait longer than we'd like, but we eventually get there - more regular updates would be nice",
            "C": "Lots of waiting around - weeks for simple decisions, causing delays and having to redo work because priorities changed",
            "D": "It's a real problem - the delays are causing major issues, missed opportunities, and everyone's getting frustrated"
        }
    },
    "Q4_Input_Involvement": {
        "question": "When changes are happening that affect your work, do you feel like anyone actually listens to what you have to say?",
        "options": {
            "A": "Absolutely! I'm regularly asked for input and can see my suggestions actually being used in the final decisions",
            "B": "Sometimes they ask, but I'm not always sure what happens with my feedback - would love to know how it's being used",
            "C": "Rarely get asked, and when I am, it feels like the decision was already made anyway",
            "D": "Never really consulted - just get told about changes after they're decided, which is frustrating given my experience"
        }
    },
    "Q5_Performance_Recognition": {
        "question": "Do you feel like your hard work gets recognized fairly, especially compared to your teammates?",
        "options": {
            "A": "Yes, the process feels fair and transparent - my contributions get the recognition they deserve",
            "B": "Mostly fair, though I'd appreciate more specific feedback and clearer criteria for what gets recognized",
            "C": "I notice some inconsistency - similar work seems to get different levels of recognition depending on who did it",
            "D": "Not really - I feel undervalued compared to my peers, and the whole process lacks transparency"
        }
    },
    "Q6_Personal_Growth": {
        "question": "Is your manager actually helping you grow in your career, especially with all the changes happening?",
        "options": {
            "A": "Definitely! We regularly talk about my development, and they're actively helping me navigate my career path",
            "B": "We have some development conversations, but they could be more frequent and focused on specific skills I need",
            "C": "Not really much happening - our development discussions are pretty rare and don't go very deep",
            "D": "Honestly, no - we hardly ever talk about my growth, and it feels like development has taken a backseat to everything else"
        }
    },
    "Q7_Tools_Resources": {
        "question": "Do you have what you need to do your job well, or are you constantly working around missing tools and resources?",
        "options": {
            "A": "I'm all set! Have everything I need to do my job effectively, plus good tech support when I need it",
            "B": "Pretty well equipped, but there are some tools or upgrades that would definitely make my work easier and better",
            "C": "Missing quite a few things I need - causes delays and I'm constantly finding workarounds, which slows me down",
            "D": "It's a real struggle - lacking basic tools and resources that seriously impact my ability to do quality work"
        }
    },
    "Q8_Follow_up_Accountability": {
        "question": "Thinking about what management promised after last year's survey - did they actually follow through on those commitments?",
        "options": {
            "A": "They really delivered! Most of what they promised actually happened, I can see real improvements, and I trust the process",
            "B": "Mixed bag - some things were done well, others not so much, but I still generally believe they're trying",
            "C": "Not much changed despite all the promises - starting to wonder if this survey actually leads to anything",
            "D": "Pretty disappointed - most commitments weren't delivered as promised, and honestly, I'm losing faith in the whole process"
        }
    },
    "Q9_Work_Environment": {
        "question": "What would make the biggest difference in making this a better place to work day-to-day?",
        "options": {
            "A": "It's already pretty good! The culture and team dynamics are supportive - just minor tweaks needed",
            "B": "Better collaboration would help - we need improved communication between teams and more inclusive decision-making",
            "C": "Some serious culture issues to fix - too much blame, office politics, or people not feeling safe to speak up",
            "D": "Major problems here - the culture is really toxic and affecting everyone's morale and well-being"
        }
    },
    "Q10_Open_Communication": {
        "question": "Can you speak up when you disagree with something or have concerns, or do you keep quiet to avoid trouble?",
        "options": {
            "A": "I feel totally comfortable speaking up about anything - leadership actually encourages different viewpoints",
            "B": "Usually comfortable, but sometimes I hold back on sensitive topics - a bit more encouragement would help",
            "C": "Depends on the topic and who I'm talking to - wish it felt more consistently safe to share honest opinions",
            "D": "I keep quiet most of the time - worried about negative consequences or getting in trouble for speaking up"
        }
    },
    "Q11_AI_Future_Readiness": {
        "question": "How do you feel about all this AI stuff coming into our work? Excited, nervous, or somewhere in between?",
        "options": {
            "A": "Bring it on! I'm excited about the possibilities and feel ready to adapt to whatever tech changes come our way",
            "B": "Interested and see the potential, but I'll definitely need some training and support to feel confident with it",
            "C": "A bit nervous but willing to learn - just need comprehensive training and ongoing support to keep up",
            "D": "Pretty worried about being left behind - concerned these changes will make my current skills irrelevant"
        }
    },
    "Q12_Most_Important_Action": {
        "question": "If you could wave a magic wand and change one thing to make your work experience better, what would it be?",
        "options": {
            "A": "Better communication - more transparency about what's happening, why decisions are made, and how changes affect me personally",
            "B": "Fix the work-life balance - realistic workloads, better time management, and actual support for managing stress",
            "C": "Invest in our people - more focus on training, career development, and helping us navigate all these changes",
            "D": "Actually listen to us - take real action on employee feedback and consistently follow through on promises"
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
    st.write("Your feedback matters! Please be honest - this is completely anonymous and confidential. If none of the options fit exactly, feel free to type your own response.")
    
    with st.form("employee_survey"):
        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        
        st.info(f"📝 Interview Session ID: **{session_id}**")
        
        responses = {}
        custom_responses = {}
        
        # Display all questions
        for question_id, question_data in SURVEY_QUESTIONS.items():
            st.subheader(f"Question {question_id.split('_')[0][1:]}")
            st.write(f"**{question_data['question']}**")
            
            # Create radio buttons with options + "Other" option
            options_list = list(question_data["options"].keys()) + ["Other (please specify)"]
            
            selected_option = st.radio(
                "Choose your response:",
                options=options_list,
                format_func=lambda x: f"{x}: {question_data['options'][x]}" if x in question_data["options"] else x,
                key=question_id
            )
            
            # If "Other" is selected, show text input
            if selected_option == "Other (please specify)":
                custom_response = st.text_area(
                    "Please share your thoughts:",
                    placeholder="Type your response here...",
                    key=f"{question_id}_custom",
                    height=100
                )
                responses[question_id] = "Other"
                custom_responses[question_id] = custom_response
            else:
                responses[question_id] = selected_option
                custom_responses[question_id] = ""
            
            # Show selected option description
            if selected_option in question_data["options"]:
                st.caption(f"💭 {question_data['options'][selected_option]}")
            
            st.write("---")
        
        # Submit button
        submitted = st.form_submit_button("📤 Submit My Response", type="primary")
        
        if submitted:
            # Validate that custom responses are filled if "Other" was selected
            validation_error = False
            for question_id, response in responses.items():
                if response == "Other" and not custom_responses[question_id].strip():
                    st.error(f"⚠️ Please provide your custom response for Question {question_id.split('_')[0][1:]}")
                    validation_error = True
            
            if not validation_error:
                # Prepare data for saving
                response_data = {
                    "session_id": session_id,
                    "timestamp": datetime.now(),
                    "responses": responses,
                    "custom_responses": custom_responses
                }
                
                # Save to MongoDB
                if save_response(response_data):
                    st.success(f"✅ Thank you! Your response has been recorded successfully!")
                    st.success(f"📋 Session ID: **{session_id}** (for your records)")
                    st.balloons()
                    
                    # Show thank you message
                    st.info("🙏 Your feedback is valuable and will help improve our workplace. Feel free to share any additional thoughts with your manager or HR team.")
                    
                    # Note about starting new survey
                    st.info("💡 To start another survey, simply refresh the page or click 'New Survey' in the sidebar.")
                else:
                    st.error("❌ Oops! Something went wrong. Please try submitting again.")

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
        # Add custom responses with _custom suffix
        if 'custom_responses' in row:
            for key, value in row['custom_responses'].items():
                if value and value.strip():  # Only add non-empty custom responses
                    flat_row[f"{key}_custom"] = value
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
        total_responses = len(analysis_df) * 12  # 12 questions
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
                if option == "Other":
                    st.write(f"**Option {option}** ({percentage:.1f}%): Custom responses (see Raw Data tab for details)")
                    # Show some custom responses if available
                    custom_col = f"{selected_question}_custom"
                    if custom_col in analysis_df.columns:
                        custom_responses = analysis_df[analysis_df[selected_question] == "Other"][custom_col].dropna()
                        if len(custom_responses) > 0:
                            st.write("📝 **Sample custom responses:**")
                            for i, response in enumerate(custom_responses.head(3), 1):
                                if response.strip():
                                    st.write(f"   {i}. \"{response[:100]}{'...' if len(response) > 100 else ''}\"")
                else:
                    st.write(f"**Option {option}** ({percentage:.1f}%): {question_data['options'][option]}")
            
            # Custom responses analysis
            custom_col = f"{selected_question}_custom"
            if custom_col in analysis_df.columns:
                custom_count = len(analysis_df[analysis_df[custom_col].notna() & (analysis_df[custom_col] != "")])
                if custom_count > 0:
                    with st.expander(f"📝 View All Custom Responses ({custom_count} responses)"):
                        custom_responses = analysis_df[analysis_df[custom_col].notna() & (analysis_df[custom_col] != "")][custom_col]
                        for i, response in enumerate(custom_responses, 1):
                            st.write(f"**{i}.** {response}")
                            st.write("---")
    
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
        
        # Display data with custom responses
        st.dataframe(filtered_df, use_container_width=True)
        
        # Show summary of custom responses if any
        custom_columns = [col for col in filtered_df.columns if col.endswith('_custom')]
        if custom_columns:
            total_custom = 0
            for col in custom_columns:
                custom_count = len(filtered_df[filtered_df[col].notna() & (filtered_df[col] != "")])
                total_custom += custom_count
            
            if total_custom > 0:
                st.info(f"📝 **{total_custom}** custom responses found in this dataset. Custom responses are shown in columns ending with '_custom'")
        
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
    
    # Add start new survey button in sidebar
    if page == "📝 New Survey":
        if st.sidebar.button("🔄 Start Fresh Survey", type="secondary"):
            st.experimental_rerun()
    
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
        - 💬 Informal, conversational questions that feel natural
        - 📝 Option to provide custom responses for any question
        - 📊 Real-time analytics and visualizations
        - 🔍 Detailed response analysis including custom feedback
        - 📈 Trend tracking over time
        - 📥 Data export capabilities
        
        **How to Use:**
        1. **New Survey**: Start a fresh interview session
        2. **Analytics**: View comprehensive analysis of collected responses
        3. **Export**: Download data for further analysis
        
        **Privacy & Security:**
        - All responses are completely anonymous
        - Data is securely stored in MongoDB
        - Session IDs are randomly generated
        - Custom responses are kept confidential
        """)
        
        st.info("💡 **Tip**: Use the Analytics section to identify areas requiring immediate attention based on survey responses. Custom responses provide valuable qualitative insights!")

if __name__ == "__main__":
    main()
