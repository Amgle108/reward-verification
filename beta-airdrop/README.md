# Silencio - Beta Airdrop

## Structure:

1. Read current users with specified league, rank bucket and lucky silencian qualification
2. Read coin allocation types from `/token_assignment`
3. Assign League Bonus to applicable users
4. Assign Rank Bonus to applicable users
5. Raffle 1000 users
    1. Order users by hashed_user_id
    2. Convert community generated string to sha256 to integer
    3. Calculate remainder dividing by number of raffle participants
    4. Assign prize to user in remainder position
6. Assign 20% of earned coins to referrer or community future bucket

## Output

### Explanation of Columns in `beta_airdrop_results/beta_airdrop_results.csv`

| Column Name                 | Description                                                                                              |
|-----------------------------|----------------------------------------------------------------------------------------------------------|
| **hashed_user_id**                 | Unique hashed identifier for the user (SHA-256).                                                      |
| **rank_bucket**             | Categorization of users based on their rank. More details in the file `/token_assignment/rank_tokens`.             |
| **league**                  | League the user belongs to.                          |
| **qualifies_lucky_silencian** | A boolean showing whether the user qualifies for the "Lucky Silencian" raffle.            |
| **SLC_rank**                | The user's SLC assigned based on rank category.                                |
| **SLC_league**              | The user's SLC assigned based on league.                  |
| **SLC_lucky**               | SLC assigned with the "Lucky Silencian" raffle. |
| **SLC**                     | The base amount of SLC assigned to the user.                                         |
| **SLC_active_amount**       | The portion of the SLC assigned directly to the user. |
| **SLC_referred_amount**     | The amount of SLC distributed to the referrer or Silencian future community bucket.    |
| **SLC_referral_amount**     | The SLC earned by the user for referring other users.                  |
| **SLC_total**               | The total SLC amount associated with the user, combining `SLC_active_amount` and `SLC_referral_amount`. |

## Requirements

The following Python libraries are required to run the notebook:

- `python==3.9.13`
- `pandas==1.5.3`
- `numpy==1.24.2`

`/token_assignment` with the following files:
- `league_tokens.csv`
- `lucky_silencian_tokens.csv`
- `rank_tokens.csv`

### Installation

1. **Set up a virtual environment** (recommended):
    ```bash
    python -m venv reward-system
    source reward-system/bin/activate     # On Windows use `reward-system\Scripts\activate`
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Usage

1. **Run script**:
    ```bash
    python beta_airdrop.py
    ```

# Verify that these are the original files used in the beta airdrop

Files were hashed and stored on chain. If you want to verify these files weren't tampered with since the beta airdrop you can follow these steps:

1. Download repository (you might get a different checksum hash if cloning the repository into some systems that add CRLF line terminators.)

2. Apply a sha256 Checksum to any of the following files (**generate sha256 file checksum**) and validate against the hashes stored on this file `beta-airdrop/hashed_files_beta_airdrop.txt`: 
- `participating_users.csv`
- `beta_airdrop.py`
- `beta_airdrop_results/beta_airdrop_results.csv`
