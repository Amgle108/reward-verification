import pandas as pd
import numpy as np
import hashlib

# set run mode
run_mode = 'slc_prizes'

## get prize distribution matrix
if run_mode == 'slc_prizes':
    input_prize_matrix = 'token_assignment/slc_prizes.csv'
    raffle_seed = 'Silencio_Raffle_Season7:Silence55%-Noise23%-Decibel13%-Frequency9%-SLC:'

prize_assignment = pd.read_csv(input_prize_matrix)
total_prize_quantity = prize_assignment['prize_quantity'].sum()
# get user data
user_data = pd.read_csv('silencio_raffle_eligible_users_september_2025.csv', dtype={'raffle_tickets': 'int64'})

user_data = user_data.sort_values(by=['raffle_tickets', 'hashed_user_id'], ascending=[False, True])
user_data['ticket_end'] = user_data['raffle_tickets'].cumsum()
user_data['ticket_start'] = user_data['ticket_end'].shift(fill_value=0) + 1 

# calculate raffle pool
raffle_pool = user_data['raffle_tickets'].sum()

# generate prize seed concatenation
prize_n_array = np.arange(1, total_prize_quantity + 1, dtype=int)
seed_concat = np.char.add(raffle_seed, prize_n_array.astype(str))

# Compute SHA-256 hashes
sha256_hashes = pd.Series(seed_concat).apply(lambda x: hashlib.sha256(x.encode()).hexdigest())

# Convert hex hashes to integers
sha256_integers = sha256_hashes.apply(lambda h: int(h, 16))

# Select tickets
selected_tickets = sha256_integers % raffle_pool + 1

# add prize metadata
allocated_prizes_df = pd.DataFrame({'prize_id':np.repeat(prize_assignment['prize_id'].values, prize_assignment['prize_quantity'].values)})
allocated_prizes_df['selected_ticket_number'] = selected_tickets.astype('int64')

# prize index
allocated_prizes_df['prize_number'] = allocated_prizes_df.index + 1

# sort for merging
allocated_prizes_df = allocated_prizes_df.sort_values(by='selected_ticket_number')

user_assigned_prizes = pd.merge_asof(
    allocated_prizes_df,
    user_data,
    left_on="selected_ticket_number",
    right_on="ticket_start",
    direction="backward" 
)

# group by prize_id and user_id
raffle_user_prizes = user_assigned_prizes.groupby(['prize_id', 'hashed_user_id']).size().reset_index(name='quantity')

# calculate amount of SLC
raffle_results = raffle_user_prizes.merge(prize_assignment[['prize_id', 'prize_value']], on='prize_id', how='left').sort_values(by='hashed_user_id')
raffle_results['amountSLC'] = raffle_results['quantity']*raffle_results['prize_value']

# add users without assigned prizes
df_missing_users = user_data[~user_data['hashed_user_id'].isin(raffle_user_prizes['hashed_user_id'].drop_duplicates())][['hashed_user_id']].reset_index(drop=True)

# Calculate the total amount of SLC per user
raffle = raffle_results.groupby('hashed_user_id')['amountSLC'].sum().reset_index()
if run_mode == 'slc_prizes':
    raffle = raffle.merge(df_missing_users, on='hashed_user_id', how='outer').fillna(0)
raffle.rename(columns={'amountSLC':'claimableAmount'}, inplace=True)

## intermediate results check
raffle_user_prizes_values = raffle_user_prizes.merge(prize_assignment[['prize_id', 'prize_name', 'prize_value']], left_on='prize_id', right_on='prize_id', how='left')
raffle_user_prizes_values['amount_slc'] = raffle_user_prizes_values['quantity']*raffle_user_prizes_values['prize_value']
raffle_user_prizes_values.groupby('prize_name')[['quantity', 'amount_slc']].sum().sort_values('quantity',ascending=False).reset_index().to_csv(f'aggregate_results/{run_mode}_raffle_prizes.csv', index=False)

# save results
results_by_user = user_data[['hashed_user_id', 'raffle_tickets']].rename(columns={'raffle_tickets':'tickets'}).merge(raffle[['hashed_user_id', 'claimableAmount']], on='hashed_user_id', how='inner')\
    .merge(raffle_user_prizes_values.pivot_table(index = 'hashed_user_id', columns='prize_name', values='quantity', fill_value = 0)
             , on='hashed_user_id', how='left').fillna(0).sort_values(['claimableAmount', 'hashed_user_id'], ascending=False)[['hashed_user_id', 'tickets', 'claimableAmount'] + prize_assignment['prize_name'].values.tolist()].to_csv(f'raffle_results/{run_mode}_raffle_results.csv', index=False)
