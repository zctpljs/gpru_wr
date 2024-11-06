import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import time

# Define a function for currency formatting (e.g., for GBP (£))
def currency_formatter(x, pos=None):
    """
    Format with £ and 2 decimal places
    """
    return f'£{x:,.2f}'

def wagering_sim_with_history_bal(start_bal, WR, av_stake, seed=None):
    """
    Simulate a wagering requirement with balance and total bet tracking.
    """
    if seed is not None:
        np.random.seed(seed)

    k = WR
    x0 = start_bal
    bal = x0
    total_bet = 0
    no_bets = 0

    history = {'spins': [0], 'balance': [round(bal, 2)], 'total_bet': [0]}

    while bal >= 0.05:
        stake = min(av_stake, bal - (bal % 0.05))
        total_bet += stake
        
        # Check if we've met the wagering requirement after updating total_bet
        if total_bet >= k * x0:
            # Record the final state when total_bet meets or exceeds the requirement
            history['spins'].append(no_bets + 1)
            history['balance'].append(bal)
            history['total_bet'].append(total_bet)
            break

        # Simulate the outcome of the spin and update balance
        xt = np.random.choice([0, 1, 3, 11], p=[0.55, 0.234, 0.21, 0.006])
        bal += stake * (xt - 1)
        bal = round(bal, 2)
        no_bets += 1

        # Record the spin details
        history['spins'].append(no_bets)
        history['balance'].append(bal)
        history['total_bet'].append(total_bet)

        # Stop if balance is insufficient for another spin
        if bal <= 0:
            break

    return pd.DataFrame(history)


def main():
    st.title("🍒 Wagering Requirement Simulator 🍒")

    st.write("""
    Welcome to the Wagering Requirement Simulator! This implements a simulation on the Behavioural Insights Team's Fruit Rush, an in-house slot game. 
             
    To win money from a wagering requirement in the UK you have to bet a certain multiple of your starting balance before you run out of money. If you go bust, you have to play with your own money. If you succeed, you can withdraw the "bonus" funds. 

    Start a simulation by clicking **"Attempt to hit the WR"**. 
             
    Have a play around with the starting balance, stake size and wagering requirement and see what impacts (i) your final balance and (ii) your chances of winning money. You can check your intuitions in section one of [BIT's technical report on wagering requirements](https://www.bi.team/publications/what-do-people-think-are-the-chances-of-winning-money-from-a-wagering-requirement-supplementary-results-to-the-main-report/).  
    """)

    # Input parameters
    start_bal = st.number_input("Starting Balance (£)", min_value=0.05, value=0.50, step=0.05)
    WR = st.number_input("Wagering Requirement Multiplier", min_value=1, value=3)
    av_stake = st.number_input("Average Stake per Spin (£)", min_value=0.05, value=0.10, step=0.05)

    # Additional settings for random seed
    with st.expander("Additional Settings"):
        seed_input = st.text_input("Random Seed (optional)", value="")
        seed = int(seed_input) if seed_input.strip().isdigit() else None

    if st.button("Attempt to hit the WR"):
        # Run the simulation
        data = wagering_sim_with_history_bal(start_bal, WR, av_stake, seed)

        # Initialize the plot with Matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Set up the WR Target line
        ax.axhline(y=WR * start_bal, color="#4D4F53", linestyle='--', label=f'WR Target ({currency_formatter(WR * start_bal)})')
        
        # Set y-axis formatting and labels
        ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
        ax.set_title('Wagering Requirement Simulation')
        ax.set_xlabel('Number of Spins')
        ax.set_ylabel('Amount (£)')
        ax.legend()

        # Set axis limits and grid, fixing the x-axis range to the total number of spins
        max_y = max(data['balance'].max(), start_bal, WR * start_bal) + 0.1
        ax.set_ylim(-0.01, max_y)
        ax.set_xlim(0, data['spins'].iloc[-1])  # Fixed x-axis range
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#EEEEEE')

        # Placeholder for the animation
        plot_placeholder = st.empty()

        # Animation loop: plot each point incrementally
        for i in range(1, len(data)):
            ax.clear()  # Clear the axis to redraw

            # Re-plot the WR Target line and set fixed x-axis range
            ax.axhline(y=WR * start_bal, color="#4D4F53", linestyle='--', label=f'WR Target ({currency_formatter(WR * start_bal)})')
            ax.plot(data['spins'][:i+1], data['total_bet'][:i+1], marker='o', color='#E59AAA', label='Total Staked', alpha=0.8)
            ax.plot(data['spins'][:i+1], data['balance'][:i+1], marker='o', color='#0098db', label='Balance', alpha=0.8)

            # Re-format y-axis with currency and set x-axis range
            ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
            ax.set_xlim(0, data['spins'].iloc[-1])  # Fixed x-axis range
            
            # Set labels, title, and legend for each frame
            ax.set_title('Wagering Requirement Simulation')
            ax.set_xlabel('Number of Spins')
            ax.set_ylabel('Amount (£)')
            ax.legend()

            # Set limits and grid for each frame
            ax.set_ylim(-0.01, max_y)
            ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#EEEEEE')
            
            # Display the updated plot
            plot_placeholder.pyplot(fig)
            
            # Small delay to control the speed of the animation
            time.sleep(1/(len(data)-1))
            

        # Display the outcome only after the animation completes
        total_bet_left = WR * start_bal - data['total_bet'].iloc[-1]
        if data['balance'].iloc[-1] <= 0:
            st.error(f"You lost with £{total_bet_left:.2f} left to bet. Try again?")
        elif data['total_bet'].iloc[-1] >= WR * start_bal:
            st.success(f"You won and would be able to take away £{data['balance'].iloc[-1]:.2f}!")
        else:
            st.info(f"You ended with £{data['balance'].iloc[-1]:.2f} and £{total_bet_left:.2f} left to bet.")

if __name__ == "__main__":
    main()

