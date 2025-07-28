import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal

from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama
from tools.news_search_tool import NewsSearchTool

load_dotenv()

class PlottingTask(BaseModel):
    symbols: list[str] = Field(..., description="List of stock ticker symbols (e.g., ['TSLA', 'AAPL']).")
    timeframe: str = Field(..., description="Time period (e.g., '1d', '1mo', '1y').")
    action: str = Field(..., description="Action to be performed, should be 'plot' or 'compare'.")

class NewsTask(BaseModel):
    ticker: str = Field(..., description="The single stock ticker symbol to search news for (e.g., 'TSLA').")
    query: str = Field(..., description="The user's specific question about the news (e.g., 'latest earnings').")

class RouterOutput(BaseModel):
    task_type: Literal['plot', 'news'] = Field(..., description="The type of task: 'plot' for charts or 'news' for analysis.")
    details: dict = Field(..., description="The structured details for the chosen task.")

llm = Ollama(model="deepseek-coder", base_url="http://localhost:11434")

router_agent = Agent(
    role="Financial Task Router",
    goal="Analyze the user's financial query and decide if it's a request for a stock PLOT/CHART or for NEWS analysis.",
    backstory="You are an intelligent routing system. You classify user requests and prepare them for the correct specialized agent team.",
    llm=llm,
    verbose=True
)

routing_task = Task(
    description="Analyze the user's query: '{query}'. Classify it as 'plot' or 'news' and extract all necessary details.",
    expected_output="A JSON object following the RouterOutput Pydantic model.",
    output_pydantic=RouterOutput,
    agent=router_agent,
)

plot_code_writer_agent = Agent(
    role="Python Developer for Financial Charting",
    goal="Write Python code to generate stock charts using yfinance, pandas, and matplotlib.",
    backstory="You are an expert in financial data visualization. You write simple, effective scripts to plot stock data.",
    llm=llm,
    verbose=True,
)

plot_code_writer_task = Task(
    description="""Based on the provided stock symbols '{symbols}', timeframe '{timeframe}', and action '{action}', write a complete Python script. The script must import necessary libraries, fetch data, generate a chart, and call `plt.show()`.""",
    expected_output="A single block of clean, executable Python code as a raw string.",
    agent=plot_code_writer_agent,
)

plot_crew = Crew(agents=[plot_code_writer_agent], tasks=[plot_code_writer_task], process=Process.sequential)

news_search_tool = NewsSearchTool()
news_analyst_agent = Agent(
    role="Financial News Analyst",
    goal="Analyze news articles to provide a concise summary that answers the user's question.",
    backstory="You are a skilled analyst who can quickly read through news reports and synthesize the key information.",
    tools=[news_search_tool],
    llm=llm,
    verbose=True,
)

news_analysis_task = Task(
    description="""Using the Financial News Search Tool, find articles for the ticker '{ticker}' relevant to '{query}'. Read the results and write a concise, bullet-point summary that answers the original question, concluding with an overall sentiment.""",
    expected_output="A well-formatted markdown string containing the summary and sentiment analysis.",
    agent=news_analyst_agent,
)

news_crew = Crew(agents=[news_analyst_agent], tasks=[news_analysis_task], process=Process.sequential)

def run_financial_analysis(query: str) -> str:
    routing_crew = Crew(agents=[router_agent], tasks=[routing_task], llm=llm)
    routing_result = routing_crew.kickoff(inputs={"query": query})
    
    router_output = RouterOutput.model_validate_json(routing_result)
    task_type = router_output.task_type
    details = router_output.details

    print(f"ROUTER DECISION: Task type is '{task_type}' with details: {details}")

    if task_type == 'plot':
        return plot_crew.kickoff(inputs=details)
    elif task_type == 'news':
        return news_crew.kickoff(inputs=details)
    else:
        return "Error: Could not determine the task type."