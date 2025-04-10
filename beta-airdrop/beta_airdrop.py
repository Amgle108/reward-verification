#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import hashlib


## get coin assignment data
league_assignment_df = pd.read_csv('token_assignment/league_tokens.csv')
rank_assignment_df = pd.read_csv('token_assignment/rank_tokens.csv')
lucky_assignment_df = pd.read_csv('token_assignment/lucky_silencian_tokens.csv')

## collect Users
# rank users by wallet balance
user_wallets = pd.read_csv('participating_users.csv', dtype={'league': str}).sort_values(by=['rank_bucket', 'hashed_user_id']).reset_index(drop=True)
user_wallets['referred_by'] = user_wallets['referred_by'].replace('', np.nan)
user_wallets[['SLC_rank', 'SLC_league', 'SLC_lucky']] = 0


## assign league bonus
for index, league_tokens in league_assignment_df.iterrows():
    # determine league
    league = league_tokens['league']
    print('processing league:', league)

    # determine user pool size and share
    league_pool = user_wallets[user_wallets['league']==league].shape[0]
    league_coin_share = league_tokens['total_tokens']/league_pool
    print(f'League pool: {league_pool} / League coin share:', league_coin_share)
    
    # assign share
    user_wallets.loc[user_wallets['league']==league, 'SLC_league'] = league_coin_share

## save league aggregate
user_wallets.groupby('league').agg(
    users = ('user_id', 'count'),
    SLC_league = ('SLC_league', 'sum')
).to_csv('aggregate_results/league_bonus_aggregate.csv')

## assign rank bonus
for index, rank_tokens in rank_assignment_df.iterrows():
    # determine rank bounds
    lower_rank = rank_tokens['lower_rank']
    upper_rank = rank_tokens['upper_rank']
    print(f'Processing ranks from {lower_rank} to {upper_rank}')
        
    # determine user pool size and share
    rank_pool = upper_rank - lower_rank + 1
    rank_coin_share = rank_tokens['total_tokens']/rank_pool
    print(f'Rank pool: {rank_pool} / Rank coin share: {rank_coin_share}')

    # assign share
    user_wallets.loc[user_wallets['rank_bucket'] == f'[{lower_rank}, {upper_rank}]', 'SLC_rank'] = rank_coin_share

## save rank bonus aggregate
user_wallets.groupby('rank_bucket').agg(
    users = ('user_id', 'count'),
    SLC_rank = ('SLC_rank', 'sum')
).sort_values('rank_bucket').to_csv('aggregate_results/rank_bonus_aggregate.csv')


## select 1000 lucky silencians

## set seed and pick winners
seed_string = 'Silencio Beta Airdrop 2025'

def pick_winner(seed, prizeid, raffle_pool):

    # generate prize sha256
    seed_prizeid = str(seed) + str(prizeid)
    sha256_hash = hashlib.sha256(seed_prizeid.encode()).hexdigest()

    # Convert hex SHA-256 to integer
    sha256_integer = int(sha256_hash, 16)
    winner_rank = sha256_integer % raffle_pool

    print(f"SHA-256 Hash (hex): {sha256_hash}")
    print(f"Winner (integer): {winner_rank}")
    return winner_rank


# determine raffle pool and coin share
raffle_pool = user_wallets[user_wallets['qualifies_lucky_silencian']==1].shape[0]
lucky1000_coin_share = lucky_assignment_df['total_tokens'][0]/1000
print(f'Lucky1000 pool: {raffle_pool} / Lucky1000 coin share: {lucky1000_coin_share}')
user_wallets = user_wallets.sort_values(by=['qualifies_lucky_silencian', 'hashed_user_id'], ascending=[False, True], na_position='last').reset_index(drop=True)

prize_id = 1
winner_ids = []

while len(winner_ids)<1000:
    # select winner
    winner_index = pick_winner(seed=seed_string, prizeid=prize_id, raffle_pool=raffle_pool)

    # if winner already selected, skip
    if winner_index in winner_ids:
        prize_id += 1
        continue
    
    # add coin share to winner
    winner_ids.append(winner_index)
    user_wallets.loc[(user_wallets['qualifies_lucky_silencian']==1) & (user_wallets.index==winner_index), 'SLC_lucky'] = lucky1000_coin_share
    prize_id += 1

## save lucky bonus aggregate
pd.DataFrame(user_wallets.agg({'user_id': 'count', 'SLC_lucky': 'sum'}).rename({'user_id': 'users'})).transpose()\
    .to_csv('aggregate_results/lucky_bonus_aggregate.csv', index=False)


user_wallets['SLC'] = user_wallets[['SLC_rank', 'SLC_league', 'SLC_lucky']].sum(axis=1)
user_wallets['SLC_active_amount'] = user_wallets['SLC']*0.8
user_wallets['SLC_referred_amount'] = user_wallets['SLC']*0.2

# assign referred bonus
user_wallets = user_wallets.merge(user_wallets.groupby('referred_by', dropna=True).agg(
        SLC_referral_amount = ('SLC_referred_amount', 'sum')
    ).reset_index().rename({'referred_by':'user_id'}, axis=1), how = 'left', on = 'user_id')
user_wallets['SLC_referral_amount'] = user_wallets['SLC_referral_amount'].fillna(0)
user_wallets['SLC_total'] = user_wallets['SLC_active_amount'] + user_wallets['SLC_referral_amount']

# checks
print(f'''Total SLC assigned: {user_wallets['SLC'].sum():.2f}''')
print(f'''Silencio referral bucket: {user_wallets["SLC_referred_amount"].sum():.2f}''')
print(f'''Silencio future community bucket: {user_wallets[user_wallets['referred_by'].isna()]['SLC_referred_amount'].sum():.2f}''')
print(f'''Silencio total assigned to referrer: {user_wallets['SLC_referral_amount'].sum():.2f}''')
print(f'''Total SLC assigned after referral: {user_wallets[user_wallets['referred_by'].isna()]['SLC_referred_amount'].sum()
               + user_wallets['SLC_referral_amount'].sum()
               + user_wallets['SLC_active_amount'].sum():.2f}''')


# save results to CSV
user_wallets[user_wallets['SLC']!=0][['hashed_user_id', 'rank_bucket', 'league', 'qualifies_lucky_silencian', 'SLC_rank', 'SLC_league', 'SLC_lucky', 'SLC', 'SLC_active_amount', 'SLC_referred_amount', 'SLC_referral_amount', 'SLC_total']].sort_values(by=['SLC_total'], ascending=False, na_position='last').to_csv('beta_airdrop_results/beta_airdrop_results.csv', index=False)
