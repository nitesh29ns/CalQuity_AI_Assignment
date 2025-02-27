# dependencies
import argparse
from langchain_groq import ChatGroq
from typing_extensions import TypedDict
from langgraph.graph import StateGraph,START,END
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import yfinance as yf
import plotly.graph_objects as go
from rich.console import Console
from rich.table import Table

# llm model api key and model name
groq_api_key = "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"
model = "llama-3.3-70b-versatile"

llm=ChatGroq(groq_api_key=groq_api_key,model_name=model)
llm

# structure model
class structure_output(BaseModel):
    """
    return the company ticker name and period only.
    """
    company_ticker : str = Field(
        description="Given a user question return the company_ticker_name only")
    
    period : str = Field(
        description="Given a user question return the period only. replace the months with mo and year with y and day with d")
    
    price : str = Field(
        description="Given a user question return the price only. replace the closing with close and opening with open and make the first letter of the price capital.")


# Prompt
system = """You have to return companies ticker name only from the question. If it's indian companies then return only national stock exchange of india ticker name only."""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)


structure_llm = llm.with_structured_output(structure_output)

ticker_name = route_prompt | structure_llm

# state class for agent maintaing the input and output
class GraphState(TypedDict):
    question: str
    company_ticker: str
    period: str
    price: str
    current_stock_value : list

# Initialize agent graph    
graph_builder=StateGraph(GraphState)

# collect relavent infomation from user query
def extractor_info_from_query(state):
  question = state['question']
  output = ticker_name.invoke(question)
  return {"company_ticker":output.company_ticker,"period":output.period,"price":output.price}


# fetech data using yfinance and plot
def extract_data_and_plot(state):
        """
        description= fetech data using yfinance and plot using plotly
        """
        ticker = state['company_ticker']
        period = state['period']
        price = state['price']

        # for more then one company
        companies = {}
        if len(ticker.split(",")) > 1:

                # download data based on the company and period
                data = yf.download(ticker,period=period,group_by="ticker")
                current_stock_value = []
                for i in range(len(ticker.split(","))):
                        com = ticker.split(",")[i].replace(" ","")
                        companies[com] = data[com].reset_index()

                        stock = yf.Ticker(com)
                        try:
                            stock_value = stock.history(period="1d")['Close'].iloc[0]
                            current_stock_value.append((com,stock_value))
                        except:
                              current_stock_value.append("not_found")

                # plot the feteched data using lines plot
                fig = go.Figure()
                for name in companies:

                        fig.add_trace(go.Scatter(x=companies[name]['Date'], y=companies[name][price], mode="lines", name=f"{name} {price} Price"))

                fig.update_layout(title=f"{ticker} Stock Price",
                        xaxis_title="Date",
                        yaxis_title="Price (USD)",
                        template="plotly_dark",
                        showlegend=True)
                
                # save the interactive plot
                fig.write_html(f"./{ticker}.html")

                fig.show()
        # for single company
        else:
                # download data based on the company and period
                data = yf.download(ticker,period=period)           
                data.reset_index(inplace=True)
                data.columns = data.columns.droplevel("Ticker")

                current_stock_value = []
                stock = yf.Ticker(ticker)
                try:
                    stock_value = stock.history(period="1d")['Close'].iloc[0]
                    current_stock_value.append((com,stock_value))
                except:
                    current_stock_value.append("not_found")

                # plot the feteched data using lines 
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data['Date'], y=data[price], mode="lines", name=f"{price} Price"))
                

                fig.update_layout(title=f"{ticker} Stock Price",
                        xaxis_title="Date",
                        yaxis_title="Price (USD)",
                        template="plotly_dark",
                        showlegend=True)
                
                # save the interactive plot
                fig.write_html(f"./{ticker}.html")

                fig.show()  

        return {"current_stock_value":current_stock_value}

# add nodes to the agent graph
graph_builder.add_node("extractor",extractor_info_from_query)
graph_builder.add_node("extract_and_plot",extract_data_and_plot)

# add edges to the agent graph
graph_builder.add_edge(START,"extractor")
graph_builder.add_edge("extractor","extract_and_plot")
graph_builder.add_edge("extract_and_plot",END)

# compile the agent
graph=graph_builder.compile()

# save the workflow of the agent
with open("agent_with_yfinance_workflow.png","wb") as file:
        file.write(graph.get_graph().draw_mermaid_png())

# for calling the agent
def start_agent(parse:str):
    # Initialize the console
    console = Console()

    table = Table(title="Addional Info")

    # Add columns
    table.add_column("Key", style="cyan", justify="left")
    table.add_column("Value", style="magenta", justify="left")

    inputs = {
        "question": parse}
    events=graph.stream(inputs)
    for i in events:
        for key, value in i.items():
            for key1, value1 in i[key].items():
                table.add_row(key1, str(value1))

    console.print("Companies Metrix", style="bold red")

    console.print(table)


      

