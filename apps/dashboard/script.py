import random
import datetime

# Sample data for random generation
clients = ["ABC Limited", "XYZ Investments", "LMN Holdings", "DEF Corp", "PQR Traders"]
locations = ["New York", "London", "Tokyo", "Dubai", "Hong Kong"]
dealers = ["Dealer1", "Dealer2", "Dealer3", "Dealer4", "Dealer5"]
stocks = [
    ("AAPL", "Apple"), ("GOOGL", "Alphabet"), ("TSLA", "Tesla"), ("AMZN", "Amazon"),
    ("MSFT", "Microsoft"), ("NFLX", "Netflix"), ("NVDA", "NVIDIA"), ("BABA", "Alibaba"),
    ("FB", "Meta"), ("AMD", "AMD"), ("INTC", "Intel"), ("IBM", "IBM"), ("ORCL", "Oracle")
]

# Function to generate random transaction records
def generate_transactions(num_entries=100):
    transactions = []
    base_date = datetime.date(2025, 3, 7)
    
    for _ in range(num_entries):
        tr_date = base_date + datetime.timedelta(days=random.randint(0, 7))
        st_date = tr_date
        time = f"{random.randint(10, 23)}:{random.randint(10, 59)}:{random.randint(10, 59)}"
        loc = random.choice(locations)
        dealer = random.choice(dealers)
        client = random.choice(clients)
        stock_symbol, stock_title = random.choice(stocks)
        buy = random.randint(10, 500)
        rate = round(random.uniform(50, 3500), 2)
        transaction_type = "BUY"
        
        transactions.append(f"{tr_date}    {st_date}    {time}    {loc}    {dealer}    {client}    Investor    USA    12345    "
                            f"Individual    12345    {client}    {stock_symbol}    {stock_title}    {buy}    0    {rate}    "
                            f"{transaction_type}    0    0    0    0    0    0    0    0    0")
    
    return "\n".join(transactions)

# Generate and print transactions
generated_data = generate_transactions(100)
print("Client Information:\n12345 ABC Limited\nTransactions:")
print("TRDATE    STDATE    TIME    LOC    DEALER    CLIENT    OCCUPATION    RESIDENCE    UIN    CLIENT_CAT    CDCID    CLIENT_TITLE    SYMBOL    SYMBOL_TITLE    BUY    SELL    RATE    FLAG    BOOK    TR_TYPE    COT_ST    KORDER    TICKET    TERMINAL    BILL    COMM    CDC    CVT    WHTS    WHTC    LAGA    SECP    NLAGA    FED    MISC")
print(generated_data)