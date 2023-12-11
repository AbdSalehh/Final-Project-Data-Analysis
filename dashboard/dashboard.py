import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import streamlit as st
import urllib
from babel.numbers import format_currency
from forex_python.converter import CurrencyRates

sns.set(style="dark")

# Helper function

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule="D", on="order_purchase_timestamp").agg(
        {"order_id": "nunique", "price": "sum"}
    )
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(
        columns={"order_id": "order_count", "price": "revenue"}, inplace=True
    )

    return daily_orders_df


def create_sum_order_items_df(df):
    sum_order_items_df = (
        df.groupby("product_category_name_english")
        .order_item_id.sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    return sum_order_items_df


def create_bypayment_df(df):
    bypayment_df = df.groupby(by="payment_type").customer_id.nunique().reset_index()
    bypayment_df.rename(columns={"customer_id": "customer_count"}, inplace=True)

    return bypayment_df


def create_byreview_df(df):
    byreview_df = df.groupby(by="review_score").customer_id.nunique().sort_values(ascending=False).reset_index()
    byreview_df.rename(columns={"customer_id": "customer_count"}, inplace=True)

    return byreview_df


def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)

    return bystate_df

def create_map_plot(data, plot, img, url, steamlit):
    brazil = img.imread(url.request.urlopen('https://i.pinimg.com/originals/3a/0c/e1/3a0ce18b3c842748c255bc0aa445ad41.jpg'),'jpg')
    fig, ax = plot.subplots(figsize=(10, 10))
    data.plot(kind="scatter", x="geolocation_lng", y="geolocation_lat", alpha=0.3, s=0.3, c='maroon', ax=ax)
    ax.axis('off')
    ax.imshow(brazil, extent=[-73.98283055, -33.8, -33.75116944, 5.4])
    steamlit.pyplot(fig)


geolocation = pd.read_csv('geolocation.csv')
map_plot_data = geolocation.drop_duplicates(subset='customer_unique_id')

# Load cleaned data
all_df = pd.read_csv("main_data.csv")

datetime_columns = ["order_purchase_timestamp", "order_estimated_delivery_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Filter data
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    
    st.title("E-Commerce Alfaduro")

    st.sidebar.image("e-commerce_logo.png", caption="E-Commerce Alfaduro", use_column_width=True, width=150, output_format="PNG")

    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label="Pilih Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date],
    )

    st.markdown("**Periode Waktu:**")
    st.markdown(f"{start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}")

main_df = all_df[
    (all_df["order_purchase_timestamp"] >= str(start_date))
    & (all_df["order_purchase_timestamp"] <= str(end_date))
]

# # Menyiapkan berbagai dataframe
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bypayment_df = create_bypayment_df(main_df)
byreview_df = create_byreview_df(main_df)
bystate_df = create_bystate_df(main_df)

# plot number of daily orders (2021)
st.header("E-Commerce Public Dataset Dashboard :sparkles:")
st.subheader("Daily Orders")

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    c = CurrencyRates()
    exchange_rate_brl_to_idr = c.get_rate('BRL', 'IDR')

    total_revenue_usd = daily_orders_df.revenue.sum()
    total_revenue_idr = total_revenue_usd * exchange_rate_brl_to_idr
    
    total_revenue = format_currency(
        total_revenue_idr, 'IDR', locale='id_ID'
    )
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker="o",
    linewidth=2,
    color="#90CAF9",
)
ax.tick_params(axis="y", labelsize=20)
ax.tick_params(axis="x", labelsize=15, rotation=45)

st.pyplot(fig)


# Product performance
st.subheader("Best & Worst Performing Product")

# Membuat subplot untuk Best Performing Product
fig, ax1 = plt.subplots(figsize=(30, 15))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x="product_category_name_english",
    y="order_item_id",
    data=sum_order_items_df.head(5),
    palette=colors,
    ax=ax1,
)
ax1.set_ylabel("Number of Sales", fontsize=30)
ax1.set_xlabel(None)
ax1.set_title("Best Performing Product", loc="center", fontsize=50)
ax1.tick_params(axis="y", labelsize=35)
ax1.tick_params(axis="x", labelsize=30, rotation=45)

for p in ax1.patches:
    ax1.annotate(f'{p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=20)

# Menampilkan plot pertama di Streamlit
st.pyplot(fig)

# Menambahkan expander untuk Best Performing Product
best_expander = st.expander("See Explanation - Best Performing Product")
best_expander.write('Seperti yang ditampilkan pada barplot di atas, dapat diketahui bahwa produk dengan performa terbaik yaitu ' + sum_order_items_df.head(1)['product_category_name_english'].values[0])

# Membuat subplot untuk Worst Performing Product
fig, ax2 = plt.subplots(figsize=(30, 15))

sns.barplot(
    x="product_category_name_english",
    y="order_item_id",
    data=sum_order_items_df.sort_values(by="order_item_id", ascending=True).head(5),
    palette=colors,
    ax=ax2,
)
ax2.set_ylabel("Number of Sales", fontsize=30)
ax2.set_xlabel(None)
ax2.set_title("Worst Performing Product", loc="center", fontsize=50)
ax2.tick_params(axis="y", labelsize=35)
ax2.tick_params(axis="x", labelsize=30, rotation=45)

# Menambahkan nilai pada barplot kedua
for p in ax2.patches:
    ax2.annotate(f'{p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=20)

# Menampilkan plot kedua di Streamlit
st.pyplot(fig)

# Menambahkan expander untuk Worst Performing Product
worst_expander = st.expander("See Explanation - Worst Performing Product")
worst_expander.write('Seperti yang ditampilkan pada barplot di atas, dapat diketahui bahwa produk dengan performa terburuk yaitu ' + sum_order_items_df.tail(1)['product_category_name_english'].values[0])

# customer demographic
st.subheader("Customer Demographics")

state_mapping = {
    'SP': '(SP) São Paulo',
    'RJ': '(RJ) Rio de Janeiro',
    'MG': '(MG) Minas Gerais',
    'RS': '(RS) Rio Grande do Sul',
    'PR': '(PR) Paraná',
    'SC': '(SC) Santa Catarina',
    'BA': '(BA) Bahia',
    'DF': '(DF) Distrito Federal',
    'ES': '(ES) Espírito Santo',
    'GO': '(GO) Goiás',
    'PE': '(PE) Pernambuco',
    'CE': '(CE) Ceará',
    'PA': '(PA) Pará',
    'MT': '(MT) Mato Grosso',
    'MA': '(MA) Maranhão',
    'MS': '(MS) Mato Grosso do Sul',
    'PB': '(PB) Paraíba',
    'PI': '(PI) Piauí',
    'RN': '(RN) Rio Grande do Norte',
    'AL': '(AL) Alagoas',
    'SE': '(SE) Sergipe',
    'TO': '(TO) Tocantins',
    'RO': '(RO) Rondônia',
    'AM': '(AM) Amazonas',
    'AC': '(AC) Acre',
    'AP': '(AP) Amapá',
    'RR': '(RR) Roraima',
}

tabs = st.tabs(["Payment Type", "Review Score", "States", "Geolocation"])

# Tab 1: Payment Type
with tabs[0]:
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.barplot(
        y="customer_count",
        x="payment_type",
        data=bypayment_df.sort_values(by="customer_count", ascending=False),
        palette=colors,
        ax=ax,
    )
    ax.set_title("Number of Customer by Payment Type", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis="x", labelsize=35)
    ax.tick_params(axis="y", labelsize=30)
    for p in ax.patches:
        ax.annotate(f'{p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=20)
    st.pyplot(fig)

    # Explanation in expander
    with st.expander("See Explanation - Payment Type"):
        st.write(
            f"Dari demografi pelanggan yang ditampilkan pada barplot di atas, dapat diketahui bahwa "
            f"tipe pembayaran {bypayment_df.loc[bypayment_df['customer_count'].idxmax(), 'payment_type']} "
            f"memiliki jumlah terbanyak, yaitu sebesar {bypayment_df['customer_count'].max():,.0f} pelanggan."
        )

# Tab 2: Review Score
with tabs[1]:
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.barplot(
        y="customer_count",
        x="review_score",
        data=byreview_df.sort_values(by="review_score", ascending=False),
        palette=colors,
        order=byreview_df['review_score'],  # Sorting from large to small
        ax=ax,
    )
    ax.set_title("Number of Customer by Review Score", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis="x", labelsize=35)
    ax.tick_params(axis="y", labelsize=30)
    for p in ax.patches:
        ax.annotate(f'{p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=20)
    st.pyplot(fig)

    # Explanation in expander
    with st.expander("See Explanation - Review Score"):
        st.write(
            f"Dari demografi pelanggan yang ditampilkan pada barplot di atas, dapat diketahui bahwa "
            f"review score dengan angka {byreview_df.loc[byreview_df['customer_count'].idxmax(), 'review_score']} "
            f"memiliki jumlah terbanyak, yaitu sebesar {byreview_df['customer_count'].max():,.0f} pelanggan."
        )

# Tab 3: States
with tabs[2]:
    bystate_df['customer_state'] = bystate_df['customer_state'].map(state_mapping)
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.barplot(
        x="customer_state",
        y="customer_count",
        data=bystate_df.sort_values(by="customer_count", ascending=False).head(5),
        palette=colors,
        ax=ax,
    )
    ax.set_title("5 States with The Largest Number of Customers", loc="center", fontsize=30)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis="y", labelsize=20)
    ax.tick_params(axis="x", labelsize=15)
    for p in ax.patches:
        ax.annotate(f'{p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=20)
    st.pyplot(fig)

    # Explanation in expander
    with st.expander("See Explanation - States"):
        st.write(
            f"Dari demografi pelanggan yang ditampilkan pada barplot di atas, dapat diketahui bahwa "
            f"Pelanggan terbanyak dari periode waktu tersebut berasal dari wilayah "
            f"{bystate_df.loc[bystate_df['customer_count'].idxmax(), 'customer_state']}, "
            f"dengan jumlah {bystate_df['customer_count'].max():,.0f} pelanggan."
        )

with tabs[3]:
    create_map_plot(map_plot_data, plt, mpimg, urllib, st)

    with st.expander("See Explanation - Geolocation"):
        st.write('Berdasarkan visualisasi yang telah disajikan, terlihat bahwa jumlah pelanggan lebih tinggi di wilayah tenggara dan selatan. Selain itu, data juga mengindikasikan bahwa kota-kota yang menjadi pusat pemerintahan, seperti São Paulo, Rio de Janeiro, Porto Alegre, dan sebagainya, memiliki jumlah pelanggan yang lebih besar.')


st.caption("Copyright © Abd. Saleh")