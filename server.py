from mcp.server.fastmcp import FastMCP
from finance_crew import run_financial_analysis

mcp = FastMCP("financial-analyst")

@mcp.tool()
def financial_assistant(query: str) -> str:
    """
    Your comprehensive financial assistant. Use this for any financial query.
    It handles stock plotting (e.g., "plot tesla vs nvidia stock for 1 year")
    and news analysis (e.g., "what is the latest news about apple's earnings?").
    Returns either Python code for plotting or a text summary for news.
    """
    try:
        result = run_financial_analysis(query)
        if "import yfinance" in result or "import matplotlib" in result:
            with open('stock_analysis.py', 'w') as f:
                f.write(result)
            return ("I have generated the Python code to create your plot. It has been saved to `stock_analysis.py`. "
                    "Please use the 'run_code' command to display the chart.")
        else:
            return result
    except Exception as e:
        return f"An error occurred: {e}"

@mcp.tool()
def run_code() -> str:
    """
    Executes the Python code located in 'stock_analysis.py'.
    Use this command after the assistant has generated the plotting code.
    """
    try:
        with open('stock_analysis.py', 'r') as f:
            code = f.read()
        exec(code)
        return "Code executed successfully. The plot should be displayed."
    except FileNotFoundError:
        return "Error: `stock_analysis.py` not found. Please ask the assistant to generate the plot code first."
    except Exception as e:
        return f"Error executing code: {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio')