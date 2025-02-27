import argparse
from agent_with_yfinance import start_agent

def parse_arguments():
    parser = argparse.ArgumentParser(description ='Enter the query')
    parser.add_argument('-query',
                    type = str,
                    help ='query contain companies name with the period and price to plot')
    return parser.parse_args()



if __name__ == "__main__":
    args = parse_arguments()
    #call the agent 
    start_agent(parse=args.query)
