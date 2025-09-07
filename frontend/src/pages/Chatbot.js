import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { apiService } from '../services/api';

const Chatbot = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: "Hi! I'm your AI assistant for lead management. I can help you find top leads, analyze performance, and answer questions about your CRM data. What would you like to know?",
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Simulate API call to chatbot service
      const response = await simulateChatbotResponse(inputMessage);
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response,
        timestamp: new Date()
      };

      setTimeout(() => {
        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
      }, 1000);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: "I'm sorry, I encountered an error. Please try again.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };

  const simulateChatbotResponse = async (message) => {
    // Simulate RAG-lite responses based on common queries
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('top leads') || lowerMessage.includes('best leads')) {
      return `Here are your top 10 leads this week:

1. **TechCorp Inc.** - 89% conversion probability, $45K revenue impact
2. **Finance Solutions** - 76% conversion probability, $32K revenue impact  
3. **HealthTech Ltd** - 68% conversion probability, $28K revenue impact
4. **DataFlow Systems** - 65% conversion probability, $25K revenue impact
5. **CloudTech Partners** - 62% conversion probability, $22K revenue impact

These leads show high engagement and strong conversion potential. I recommend prioritizing calls to the top 3 leads immediately.`;
    }
    
    if (lowerMessage.includes('conversion rate') || lowerMessage.includes('performance')) {
      return `Your current conversion metrics:

📊 **Overall Performance:**
- Conversion Rate: 23.4% (up 2.1% from last month)
- Total Pipeline Value: $2.84M
- High Priority Leads: 89
- Average Deal Size: $12,500

📈 **Trends:**
- Leads are up 15% this month
- Email engagement increased by 8%
- Call response rate improved to 34%

The AI model is performing well with 94% accuracy in predictions.`;
    }
    
    if (lowerMessage.includes('industry') || lowerMessage.includes('sector')) {
      return `Industry breakdown of your leads:

🏢 **Top Performing Industries:**
1. Technology - 28% of leads, 31% conversion rate
2. Finance - 22% of leads, 26% conversion rate
3. Healthcare - 18% of leads, 24% conversion rate
4. E-commerce - 15% of leads, 21% conversion rate
5. Manufacturing - 12% of leads, 19% conversion rate

Technology and Finance sectors show the highest conversion rates and deal sizes. Consider focusing your outreach efforts on these industries.`;
    }
    
    if (lowerMessage.includes('action') || lowerMessage.includes('next step')) {
      return `Recommended actions for today:

🎯 **Immediate Actions (Next 2 hours):**
- Call 5 high-priority leads (TechCorp, Finance Solutions, HealthTech)
- Send follow-up emails to 12 warm leads
- Schedule demos for 3 qualified prospects

📧 **Email Campaigns:**
- Nurture sequence for 45 medium-priority leads
- Re-engagement campaign for 23 dormant leads
- Industry-specific content for 67 new leads

📊 **Analytics Review:**
- Check conversion funnel performance
- Review A/B test results for email templates
- Analyze competitor activity in your top industries`;
    }
    
    if (lowerMessage.includes('revenue') || lowerMessage.includes('pipeline')) {
      return `Revenue and pipeline analysis:

💰 **Pipeline Value: $2.84M**
- High probability deals: $1.2M (42%)
- Medium probability deals: $1.1M (39%)
- Low probability deals: $540K (19%)

📈 **Revenue Forecast:**
- This month: $340K (based on current pipeline)
- Next month: $420K (with new leads)
- Quarter target: $1.2M (on track)

🎯 **Top Revenue Opportunities:**
1. TechCorp Inc. - $45K (89% probability)
2. Finance Solutions - $32K (76% probability)
3. HealthTech Ltd - $28K (68% probability)

Focus on closing the high-probability deals first to maximize revenue.`;
    }
    
    if (lowerMessage.includes('help') || lowerMessage.includes('what can you do')) {
      return `I can help you with:

🔍 **Lead Analysis:**
- Find top performing leads
- Analyze conversion patterns
- Identify high-value opportunities

📊 **Performance Insights:**
- Conversion rate analysis
- Industry performance breakdown
- Revenue forecasting

🎯 **Action Planning:**
- Next best actions for leads
- Priority recommendations
- Campaign suggestions

💡 **Quick Queries:**
- "Show me top 10 leads this week"
- "What's our conversion rate by industry?"
- "Which leads need immediate attention?"
- "What's our revenue forecast?"

Just ask me anything about your leads and I'll provide insights!`;
    }
    
    // Default response
    return `I understand you're asking about "${message}". 

I can help you analyze your leads, check performance metrics, find top opportunities, or answer questions about your CRM data. 

Try asking me:
- "Who are my top 10 leads this week?"
- "What's our conversion rate by industry?"
- "Show me leads that need immediate attention"
- "What's our revenue forecast?"

What specific information would you like to know?`;
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickQuestions = [
    "Who are my top 10 leads this week?",
    "What's our conversion rate?",
    "Show me high-priority leads",
    "What's our revenue forecast?"
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="p-6 border-b">
        <h1 className="text-2xl font-bold text-gray-900">AI Assistant</h1>
        <p className="text-gray-600">Ask me anything about your leads and CRM data</p>
      </div>

      {/* Quick Questions */}
      <div className="p-4 bg-gray-50 border-b">
        <p className="text-sm text-gray-600 mb-2">Quick questions:</p>
        <div className="flex flex-wrap gap-2">
          {quickQuestions.map((question, index) => (
            <button
              key={index}
              onClick={() => setInputMessage(question)}
              className="px-3 py-1 bg-white border rounded-full text-sm text-gray-700 hover:bg-blue-50 hover:border-blue-300 transition-colors"
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`flex max-w-xs lg:max-w-md ${
                message.type === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white ml-2'
                    : 'bg-gray-200 text-gray-600 mr-2'
                }`}
              >
                {message.type === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </div>
              <div
                className={`px-4 py-2 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border text-gray-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex max-w-xs lg:max-w-md">
              <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 mr-2 flex items-center justify-center">
                <Bot className="w-4 h-4" />
              </div>
              <div className="px-4 py-2 rounded-lg bg-white border">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-white">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about your leads..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
