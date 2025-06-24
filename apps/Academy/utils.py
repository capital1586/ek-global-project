from django.utils import timezone
from datetime import timedelta
import random
from .models import Video, Course, LearningOutcome, NewsArticle, Benefit

def create_mock_data():
    """Create mock data for testing the Academy app"""
    
    # Create benefits
    if Benefit.objects.count() == 0:
        benefits = [
            {
                'title': 'Expert Instructors',
                'description': 'Learn from industry professionals with years of experience in financial markets and trading.',
                'icon': 'fas fa-graduation-cap'
            },
            {
                'title': 'Practical Learning',
                'description': 'Apply concepts with real-world examples and case studies from actual market scenarios.',
                'icon': 'fas fa-laptop'
            },
            {
                'title': 'Market Insights',
                'description': 'Stay updated with current market trends and analysis from our team of researchers.',
                'icon': 'fas fa-chart-line'
            },
            {
                'title': 'Community Support',
                'description': 'Connect with fellow traders and investors to share ideas and strategies.',
                'icon': 'fas fa-users'
            }
        ]
        
        for benefit_data in benefits:
            Benefit.objects.create(**benefit_data)
    
    # Create courses
    if Course.objects.count() == 0:
        courses_data = [
            {
                'title': 'Technical Analysis Fundamentals',
                'description': """
                Master the art of technical analysis with our comprehensive course designed for traders of all levels.
                
                In this course, you'll learn how to read and interpret price charts, identify key patterns, and make 
                informed trading decisions based on technical indicators. From support and resistance levels to moving 
                averages and oscillators, we cover all the essential tools you need to analyze market movements.
                
                The course includes practical exercises and real-world trading scenarios to help you apply your knowledge 
                effectively. By the end of this course, you'll have a solid foundation in technical analysis that you can 
                apply to any financial market.
                """,
                'image': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=1470&auto=format&fit=crop',
            },
            {
                'title': 'Fundamental Analysis for Investors',
                'description': """
                Gain a deep understanding of fundamental analysis to make smarter long-term investment decisions.
                
                This course teaches you how to evaluate a company's financial health, analyze industry trends, and 
                understand economic factors that influence market performance. You'll learn to read financial statements, 
                calculate key ratios, and determine the intrinsic value of stocks.
                
                Through case studies of successful investors and real company analyses, you'll develop the skills to 
                identify undervalued stocks with strong growth potential. Whether you're a beginner or experienced 
                investor, this course will enhance your ability to build a profitable investment portfolio.
                """,
                'image': 'https://images.unsplash.com/photo-1633158829875-e5316a358c6f?q=80&w=1470&auto=format&fit=crop',
            },
            {
                'title': 'Risk Management Strategies',
                'description': """
                Learn essential risk management techniques to protect your capital and optimize your trading results.
                
                This course focuses on the critical aspect of trading that many overlook: risk management. You'll learn 
                how to set appropriate stop losses, calculate position sizes, and implement various hedging strategies
                to minimize potential losses.
                
                We cover diversification techniques, risk-reward ratios, and portfolio allocation models that can help
                you survive market downturns and maintain consistent profitability. Through practical examples and
                interactive exercises, you'll develop a robust risk management framework that you can apply to your
                own trading strategy.
                """,
                'image': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=1415&auto=format&fit=crop',
            }
        ]
        
        for course_data in courses_data:
            course = Course.objects.create(**course_data)
            
            # Create learning outcomes for each course
            if course.title == 'Technical Analysis Fundamentals':
                outcomes = [
                    'Understand and interpret various chart patterns',
                    'Apply technical indicators to identify trading opportunities',
                    'Analyze market trends and determine market direction',
                    'Use support and resistance levels effectively',
                    'Implement various technical trading strategies',
                    'Identify entry and exit points using technical analysis'
                ]
            elif course.title == 'Fundamental Analysis for Investors':
                outcomes = [
                    'Read and analyze financial statements',
                    'Calculate and interpret key financial ratios',
                    'Evaluate company performance and industry position',
                    'Assess company management and governance',
                    'Determine intrinsic value using various valuation models',
                    'Make investment decisions based on fundamental analysis'
                ]
            else:  # Risk Management Strategies
                outcomes = [
                    'Calculate appropriate position sizes based on risk tolerance',
                    'Set effective stop-loss and take-profit levels',
                    'Implement portfolio diversification strategies',
                    'Manage drawdowns and preserve capital during losing streaks',
                    'Understand and apply the Kelly Criterion for optimal bet sizing',
                    'Create a comprehensive risk management plan'
                ]
            
            for outcome in outcomes:
                LearningOutcome.objects.create(course=course, outcome=outcome)
            
            # Create videos for each course
            create_mock_videos(course)
    
    # Create news articles
    if NewsArticle.objects.count() == 0:
        create_mock_news()

def create_mock_videos(course=None):
    """Create mock YouTube videos"""
    
    # Sample video data for different courses
    tech_analysis_videos = [
        {
            'title': 'Introduction to Technical Analysis',
            'youtube_id': 'dD5ZqVmQRZg',
            'description': 'Learn the basics of technical analysis and how to read price charts.',
        },
        {
            'title': 'Support and Resistance Levels Explained',
            'youtube_id': 'LwUibOIAgek',
            'description': 'Understanding support and resistance levels and how to use them in trading.',
        },
        {
            'title': 'Moving Averages - Simple and Exponential',
            'youtube_id': '8TiuJm7rG1I',
            'description': 'How to use moving averages to identify trends and potential reversals.',
        },
        {
            'title': 'RSI and MACD Indicators',
            'youtube_id': '9LZ8cJWBLlo',
            'description': 'Learn how to use the RSI and MACD indicators to identify overbought and oversold conditions.',
        }
    ]
    
    fundamental_analysis_videos = [
        {
            'title': 'Introduction to Fundamental Analysis',
            'youtube_id': 'rNlAGp9Bp2A',
            'description': 'Learn the basics of fundamental analysis and how to evaluate companies.',
        },
        {
            'title': 'Reading Financial Statements',
            'youtube_id': 'D7rACTLiq_8',
            'description': 'How to read and analyze income statements, balance sheets, and cash flow statements.',
        },
        {
            'title': 'Valuation Methods for Stocks',
            'youtube_id': '2AiWLwtN72c',
            'description': 'Different methods to value stocks including DCF, P/E ratios, and more.',
        },
        {
            'title': 'Economic Indicators and Their Impact',
            'youtube_id': 'DX5TXdmQ56M',
            'description': 'Understanding economic indicators and how they affect the stock market.',
        }
    ]
    
    risk_management_videos = [
        {
            'title': 'Introduction to Risk Management',
            'youtube_id': 'S_Uvy_VFpA8',
            'description': 'Learn the importance of risk management in trading and investing.',
        },
        {
            'title': 'Position Sizing Techniques',
            'youtube_id': 'PZa9LIiN5JQ',
            'description': 'How to determine the right position size for your trades based on risk tolerance.',
        },
        {
            'title': 'Stop Loss Strategies',
            'youtube_id': 'KFRnt3JJF5g',
            'description': 'Different approaches to setting stop losses to protect your capital.',
        },
        {
            'title': 'Portfolio Diversification',
            'youtube_id': 'QfPy2Qu7_EQ',
            'description': 'How to diversify your portfolio to reduce risk and improve returns.',
        }
    ]
    
    # Select the appropriate video list based on the course
    if course:
        if course.title == 'Technical Analysis Fundamentals':
            videos_data = tech_analysis_videos
        elif course.title == 'Fundamental Analysis for Investors':
            videos_data = fundamental_analysis_videos
        else:  # Risk Management Strategies
            videos_data = risk_management_videos
        
        # Create videos for the specific course
        for i, video_data in enumerate(videos_data):
            # Set published date with decreasing order (newest first)
            published_date = timezone.now() - timedelta(days=i*3)
            Video.objects.create(
                course=course,
                published_date=published_date,
                **video_data
            )
    else:
        # Create some non-course videos
        general_videos = [
            {
                'title': 'Market Outlook for 2024',
                'youtube_id': 'v_Jw5ZKVoV8',
                'description': 'Analysis of current market trends and outlook for the upcoming year.',
            },
            {
                'title': 'Trading Psychology - Overcoming Emotions',
                'youtube_id': 'lZRMVGk8mRY',
                'description': 'How to manage emotions and develop a trader\'s mindset.',
            },
            {
                'title': 'Introduction to Cryptocurrencies',
                'youtube_id': 'rYQgy8QDEBI',
                'description': 'Understanding the basics of cryptocurrencies and blockchain technology.',
            }
        ]
        
        for i, video_data in enumerate(general_videos):
            published_date = timezone.now() - timedelta(days=i*2)
            Video.objects.create(
                published_date=published_date,
                **video_data
            )

def create_mock_news():
    """Create mock news articles"""
    
    news_data = [
        {
            'title': 'Federal Reserve Holds Interest Rates Steady',
            'content': 'The Federal Reserve announced today that it will keep interest rates unchanged, citing stable inflation and continued economic growth. Analysts had widely expected this decision, though some had predicted a potential rate cut.',
            'source': 'Financial Times',
            'url': 'https://www.ft.com',
            'image_url': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=1470&auto=format&fit=crop'
        },
        {
            'title': 'Tech Stocks Rally as Earnings Beat Expectations',
            'content': 'Major technology companies reported stronger-than-expected earnings for the latest quarter, driving a rally in tech stocks. Companies including Apple, Microsoft, and Amazon all exceeded analyst projections.',
            'source': 'Wall Street Journal',
            'url': 'https://www.wsj.com',
            'image_url': 'https://images.unsplash.com/photo-1642543492523-e81bd7e28ce1?q=80&w=1470&auto=format&fit=crop'
        },
        {
            'title': 'Oil Prices Drop Amid Increased Production',
            'content': 'Crude oil prices fell by 3% today after OPEC+ announced plans to increase production quotas. The move comes as global demand forecasts have been revised upward for the coming year.',
            'source': 'Bloomberg',
            'url': 'https://www.bloomberg.com',
            'image_url': 'https://images.unsplash.com/photo-1582182833710-1c776b231ecf?q=80&w=1470&auto=format&fit=crop'
        },
        {
            'title': 'New Regulations Proposed for Cryptocurrency Markets',
            'content': 'Regulatory authorities have proposed new guidelines for cryptocurrency exchanges and trading platforms. The regulations aim to increase transparency and protect investors while still allowing for innovation in the sector.',
            'source': 'Reuters',
            'url': 'https://www.reuters.com',
            'image_url': 'https://images.unsplash.com/photo-1518546305927-5a555bb7020d?q=80&w=1470&auto=format&fit=crop'
        },
        {
            'title': 'Global Supply Chain Issues Easing, Report Finds',
            'content': 'A new report indicates that global supply chain disruptions are beginning to ease after two years of significant challenges. Shipping costs have decreased, and delivery times have improved across most sectors.',
            'source': 'CNBC',
            'url': 'https://www.cnbc.com',
            'image_url': 'https://images.unsplash.com/photo-1566576721346-d4a3b4eaeb55?q=80&w=1470&auto=format&fit=crop'
        },
        {
            'title': 'Banking Sector Shows Resilience in Stress Tests',
            'content': 'The latest round of banking stress tests shows that major financial institutions remain well-capitalized and could withstand a severe economic downturn. Regulators expressed satisfaction with the overall health of the banking system.',
            'source': 'Financial Times',
            'url': 'https://www.ft.com',
            'image_url': 'https://images.unsplash.com/photo-1501167786227-4cba60f6d58f?q=80&w=1470&auto=format&fit=crop'
        },
        {
            'title': 'Emerging Markets Face Currency Pressures',
            'content': 'Several emerging market economies are experiencing significant currency depreciation against the US dollar. Central banks in these countries have begun intervening to stabilize their currencies and control inflation.',
            'source': 'The Economist',
            'url': 'https://www.economist.com',
            'image_url': 'https://images.unsplash.com/photo-1604594849809-dfedbc827105?q=80&w=1470&auto=format&fit=crop'
        },
        {
            'title': 'Renewable Energy Investments Hit Record High',
            'content': 'Global investments in renewable energy sources reached an all-time high last quarter, driven by significant commitments from both private companies and governments worldwide. Solar and wind projects attracted the majority of funding.',
            'source': 'Bloomberg',
            'url': 'https://www.bloomberg.com',
            'image_url': 'https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?q=80&w=1470&auto=format&fit=crop'
        }
    ]
    
    for i, article_data in enumerate(news_data):
        # Create articles with staggered publish dates (newest first)
        published_date = timezone.now() - timedelta(days=i)
        NewsArticle.objects.create(
            published_date=published_date,
            **article_data
        ) 