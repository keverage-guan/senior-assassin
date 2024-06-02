import os
import discord
import pandas as pd
import random
from discord.ext import commands
from env import DISCORD_TOKEN
import dataframe_image as dfi

TOKEN = DISCORD_TOKEN

intents = discord.Intents.default()
intents.guild_messages = True

client = commands.Bot(command_prefix=">", intents=discord.Intents.all())

command_channel_id = 1103332450547028139
admin_channel_id = 1103332581237346356
announce_id = 1102707017291923536
announcements = None

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('Senior Assassin'))
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global command_channel_id
    global admin_channel_id
    global announce_id
    global announcements

    if announce_id != None:
        global announcements
        announcements = client.get_channel(announce_id)

    if message.author != client.user:
        if (admin_channel_id is None or message.channel.id == admin_channel_id):
            if message.content.startswith('/channels'):
                # Send a message with the current channel IDs
                await message.channel.send(f'Admin channel: <#{admin_channel_id}>\nCommand channel: <#{command_channel_id}>\nAnnouncement channel: <#{announce_id}>')

            if message.content.startswith('/set'):
                # Make sure there is one argument
                if len(message.content.split(' ')) != 3:
                    await message.channel.send('Invalid number of arguments. Please use the format /channel <admin, command, or announce> <channel id>')
                    return
                # Extract the channel ID from the command message
                command, channel_type, channel_id_str = message.content.split(' ')
                channel_id = int(channel_id_str)

                # if channel_type is not admin, command, or announce, say so and return
                if channel_type not in ['admin', 'command', 'announce']:
                    await message.channel.send('Invalid channel type. Please use the format /channel <admin, command, or announce> <channel id>')
                    return
                
                # if channel_type is admin, set admin_channel_id to channel_id
                if channel_type == 'admin':
                    admin_channel_id = channel_id
                    if command_channel_id == None:
                        command_channel_id = admin_channel_id

                    if announce_id == None:
                        announce_id = admin_channel_id

                # if channel_type is command, set command_channel_id to channel_id
                elif channel_type == 'command':
                    command_channel_id = channel_id

                # if channel_type is announce, set announce_id to channel_id
                elif channel_type == 'announce':
                    announce_id = channel_id
                
                # Send a message to confirm the channel has been set
                await message.channel.send(f'Channel <#{channel_id}> set to {channel_type} channel.')

            elif message.content.startswith('/eliminate'):
                # make sure there are two arguments
                if len(message.content.split(' ')) == 3:
                    df = pd.read_excel('responses.xlsx', sheet_name='responses')

                    # get argument
                    command, team, player = message.content.split(' ')
                    team = int(team)
                    player = int(player)

                    # if player is 1, set p1 of that team to dead, else set p2 of that team to dead
                    if player == 1:
                        df.loc[df['number'] == team, 'status1'] = 'dead'
                    elif player == 2:
                        df.loc[df['number'] == team, 'status2'] = 'dead'

                    # get player name
                    player_name = df.loc[df['number'] == team, f'p{player}'].tolist()[0]

                    # save to excel
                    df.to_excel('responses.xlsx', sheet_name='responses', index=False)

                    await announcements.send(f'Team {team}\'s {player_name} has been eliminated! :gun:')
                    return

                elif len(message.content.split(' ')) != 4:
                    await message.channel.send('Invalid number of arguments. Please use the format /eliminate <assassin number> <target team number> <player 1 or 2>')
                    return
                
                # get arguments
                if len(message.content.split(' ')) == 4:
                    command, assassin, target_team, target_player = message.content.split(' ')

                # read in sheet responses in xlsx responses
                df = pd.read_excel('responses.xlsx', sheet_name='responses')

                # get row where number is assassin
                assassin_row = df.loc[df['number'] == int(assassin)]

                # if assassin is dead, say so and return
                if assassin_row['status1'].tolist()[0] == 'dead' and assassin_row['status2'].tolist()[0] == 'dead':
                    await message.channel.send('Assassin is already dead!')
                    return
                
                # get row of target team
                target_row = df.loc[df['number'] == int(target_team)]

                # if target player is already dead, say so and return
                if (target_player == '1' and target_row['status1'].tolist()[0] == 'dead') or (target_player == '2' and target_row['status2'].tolist()[0] == 'dead'):
                    await message.channel.send('Target player is already dead!')
                    return
                
                # set status of target player to dead
                if target_player == '1':
                    df.loc[df['number'] == int(target_team), 'status1'] = 'dead'
                elif target_player == '2':
                    df.loc[df['number'] == int(target_team), 'status2'] = 'dead'

                # set 'remaining' column for that team -1
                df.loc[df['number'] == int(target_team), 'remaining'] -= 1
                
                # get team name of assassin and target and eliminated player name
                assassin_team = df.loc[df['number'] == int(assassin), 'team'].tolist()[0]
                target_team_name = df.loc[df['number'] == int(target_team), 'team'].tolist()[0]
                eliminated_player = df.loc[df['number'] == int(target_team), f'p{target_player}'].tolist()[0]

                # add kill to assassin team
                df.loc[df['number'] == int(assassin), ' total kills '] += 1
                df.loc[df['number'] == int(assassin), ' weekly kills '] += 1

                # send elimination message
                await announcements.send(f'Team {assassin_team} has eliminated team {target_team_name}\'s {eliminated_player}! Team {assassin_team} now has {df.loc[df["number"] == int(assassin), " total kills "].tolist()[0]} kill(s). :gun:')

                # if remaining is 0, send elimination message
                if df.loc[df['number'] == int(target_team), 'remaining'].tolist()[0] == 0:
                    await announcements.send(f'Team {target_team_name} has been eliminated! :skull:')
                    # set column 'safety' for that team to nothing
                    df.loc[df['number'] == int(target_team), 'safety'] = ''

                # save to excel
                df.to_excel('responses.xlsx', sheet_name='responses', index=False)

            elif message.content.startswith('/revive'):
                # make sure there are two arguments
                if len(message.content.split(' ')) != 3:
                    await message.channel.send('Invalid number of arguments. Please use the format /revive <team number> <player 1 or 2>')
                    return
                # get argument
                command, team, player = message.content.split(' ')
                team = int(team)
                player = int(player)

                # read in sheet responses in xlsx responses
                df = pd.read_excel('responses.xlsx', sheet_name='responses')

                # set status of that player to alive
                if player == 1:
                    df.loc[df['number'] == team, 'status1'] = 'alive'
                elif player == 2:
                    df.loc[df['number'] == team, 'status2'] = 'alive'

                # set 'remaining' column for that team +1
                df.loc[df['number'] == team, 'remaining'] += 1

                # save to excel
                df.to_excel('responses.xlsx', sheet_name='responses', index=False)

                # get player name
                player_name = df.loc[df['number'] == team, f'p{player}'].tolist()[0]

                await announcements.send(f'Team {team}\'s {player_name} has been revived! :innocent:')

            elif message.content.startswith('/shuffle'):
                await announcements.send('Shuffling teams (for real this time)...')

                # if targets column exists, drop
                df = pd.read_excel('responses.xlsx', sheet_name='responses')
                if 'target' in df.columns:
                    df = df.drop(['target'], axis=1)

                # add an empty column called target
                df['target'] = ''

                # create a list of all team numbers where at least one status is alive
                alive = df.loc[(df['status1'] == 'alive') | (df['status2'] == 'alive'), 'number'].tolist()

                # randomly shuffle alive
                random.shuffle(alive)

                # for each team number in alive, set target to the next team number in alive and make the first team the target of the last team
                for i in range(len(alive)):
                    if i == len(alive) - 1:
                        df.loc[df['number'] == alive[i], 'target'] = alive[0]
                    else:
                        df.loc[df['number'] == alive[i], 'target'] = alive[i+1]

                #for every row, if a player is alive and weekly kills is 0, set safety to no, if a player is alive and weekly kills is non-zero, set safety to yes
                for index, row in df.iterrows():
                    if (row['status1'] == 'alive' or row['status2'] == 'alive') and row[' weekly kills '] == 0:
                        df.loc[index, 'safety'] = 'no'
                    elif (row['status1'] == 'alive' or row['status2'] == 'alive') and row[' weekly kills '] > 0:
                        df.loc[index, 'safety'] = 'yes'

                # clear weekly kills
                df[' weekly kills '] = 0

                # for member in all members
                for member in message.guild.members:
                    # get row where discord1 or discord2 is member's tag
                    if ('#' + str(member.id)) in df['discord1'].tolist():
                        row = df.loc[df['discord1'] == ('#' + str(member.id))]
                    elif ('#' + str(member.id)) in df['discord2'].tolist():
                        row = df.loc[df['discord2'] == ('#' + str(member.id))]
                    else: 
                        continue

                    # continue if both members are dead
                    if row['status1'].tolist()[0] == 'dead' and row['status2'].tolist()[0] == 'dead':
                        continue

                    # get target number of row
                    target = row['target'].tolist()[0]

                    # get target information
                    target_row = df.loc[df['number'] == target]
                    target_p1 = target_row['p1'].tolist()[0]
                    target_p2 = target_row['p2'].tolist()[0]
                    target_team = target_row['team'].tolist()[0]
                    status1 = target_row['status1'].tolist()[0]
                    status2 = target_row['status2'].tolist()[0]

                    # dm member their target information "Your target team is team {team} with players {p1} (status) and {p2} (status). Good luck!"
                    try: 
                        await member.send(f'This is not a test. Your next target team is team {target_team} with players {target_p1} ({status1}) and {target_p2} ({status2}). Good luck!')
                    except:
                        # say failed to dm member in admin channel
                        await message.channel.send(f'Failed to dm {member}.')

                # delete targets column
                df = df.drop(['target'], axis=1)

                # save to excel
                #df.to_excel('responses.xlsx', sheet_name='responses', index=False)

                await announcements.send('@everyone New targets have been assigned (for real this time)! :dart:')

            elif message.content.startswith('/kills'):
                #make sure there are two arguments
                if len(message.content.split(' ')) != 3:
                    await message.channel.send('Invalid number of arguments. Please use the format /kills <team number> <kills>')
                    return
                
                # get arguments
                command, team, kills = message.content.split(' ')
                team = int(team)
                kills = int(kills)

                # read in sheet responses in xlsx responses
                df = pd.read_excel('responses.xlsx', sheet_name='responses')

                # set kills column of that team to kills
                df.loc[df['number'] == team, ' total kills '] = kills

                # save to excel
                df.to_excel('responses.xlsx', sheet_name='responses', index=False)

                await announcements.send(f'Team {team}\'s kill count has been set to {kills}.')

            elif message.content.startswith('/quit'):
                if str(message.author) == 'bevin#2665':
                    try:
                        await message.channel.send("Shutting down...")
                        await client.close()
                    except:
                        print("EnvironmentError")
                        client.clear()
                else:
                    await message.channel.send("You do not own this bot!")

            elif message.content.startswith('/replace'):
                # go through members in guild, if in discord1 or discord2, replace with str(member.id)
                df = pd.read_excel('responses.xlsx', sheet_name='responses')

                for member in message.guild.members:
                    if str(member) in df['discord1'].tolist():
                        df.loc[df['discord1'] == str(member), 'discord1'] = str(member.id)
                    elif str(member) in df['discord2'].tolist():
                        df.loc[df['discord2'] == str(member), 'discord2'] = str(member.id)

                df.to_excel('responses.xlsx', sheet_name='responses', index=False)


        if message.channel.id == command_channel_id or message.channel.id == admin_channel_id:
            if message.content.startswith('/scoreboard'):
                # if 1 argument, store as sort, else sort defaults to kills
                if len(message.content.split(' ')) == 2:
                    command, sort = message.content.split(' ')
                else:
                    sort = ' total kills '

                # read in sheet responses in xlsx responses
                df = pd.read_excel('responses.xlsx', sheet_name='responses')

                # if sort is not kills, number, p1, status1, status2, p2, team, or remaining, say so and return
                if sort not in [' weekly kills ',' total kills ', 'number', 'p1', 'status1', 'status2', 'p2', 'team', 'remaining']:
                    await message.channel.send('Invalid sort. Please use the format /scoreboard <column>')
                    return

                # sort by sort, descending if kills or remaining and ascending otherwise
                # if kills, do kills then remaining, if remaining, do remaining then kills
                if sort == ' total kills ':
                    df = df.sort_values(by=[' total kills ', ' weekly kills ', 'remaining'], ascending=False)
                elif sort == 'remaining':
                    df = df.sort_values(by=['remaining', ' total kills ', ' weekly kills '], ascending=False)
                elif sort == ' weekly kills ':
                    df = df.sort_values(by=[' weekly kills ', ' total kills ', 'remaining'], ascending=False)
                else:
                    df = df.sort_values(by=[sort], ascending=True)

                df.drop(['email', 'discord1', 'discord2'], axis=1, inplace=True)

                # for each team, check if greater than 12 characters. if it is, truncate to 12 characters and add ...
                for index, row in df.iterrows():
                    if len(row['team']) > 12:
                        df.loc[index, 'team'] = row['team'][:12] + '...' 

                # truncate p1 and p2 to first name + first letter after
                df['p1'] = df['p1'].str.split(' ').str[0] + ' ' + df['p1'].str.split(' ').str[1].str[0]
                df['p2'] = df['p2'].str.split(' ').str[0] + ' ' + df['p2'].str.split(' ').str[1].str[0]

                # style data frame: text of p1 and status1 are green if status1 is alive. red if dead. same for p2 and status2. also hide indices
                def color_alive_red_dead(val):
                    color = 'red' if val == 'dead' else 'green'
                    return 'color: %s' % color

                # set up dataframe image
                for i in range(0, len(df), 14):
                    # style df so red/green setup is applied
                    dfi.export(df[i:i+14].style.set_properties(**{'text-align': 'center'}).applymap(color_alive_red_dead, subset=['status1', 'status2']), f'scoreboard.png', table_conversion='matplotlib')

                    with open('scoreboard.png', 'rb') as f:
                        picture = discord.File(f)
                        await message.channel.send(file=picture)

            elif message.content.startswith('/info'):
                # check if 1 argument else return
                if len(message.content.split(' ')) != 2:
                    await message.channel.send('Invalid number of arguments. Please use the format /team <team number>')
                    return
                
                # get argument
                command, number = message.content.split(' ')
                number = int(number)

                # read in sheet responses in xlsx responses
                df = pd.read_excel('responses.xlsx', sheet_name='responses')

                # if number is not in df, say so and return
                if number not in df['number'].tolist():
                    await message.channel.send('Team number not found!')
                    return
                
                # get row where number is number
                row = df.loc[df['number'] == number]

                # get team name, p1, p2, and status
                team = row['team'].tolist()[0]
                p1 = row['p1'].tolist()[0]
                p1_status = row['status1'].tolist()[0]
                p2 = row['p2'].tolist()[0]
                p2_status = row['status2'].tolist()[0]
                total_kills = row[' total kills '].tolist()[0]
                weekly_kills = row[' weekly kills '].tolist()[0]
                safety = row['safety'].tolist()[0]

                # send message with team name, p1, p2, and status
                await message.channel.send(f'Team: {team}\nPlayer 1: {p1} ({p1_status})\nPlayer 2: {p2} ({p2_status})\nTotal Kills: {total_kills}\nWeekly Kills: {weekly_kills}\nSafety Item: {safety}')
                return
            
            elif message.content.startswith('/truth1'):
                await message.channel.send(f'Kevin G and Michael Gao are the best assassins :smiling_face_with_3_hearts:')

            elif message.content.startswith('/truth2'):
                await message.channel.send(f'Don\'t kill Kevin he\'s a nice guy :pleading_face:')

            elif 'best' in message.content.lower():
                if str(message.author) == 'bevin#2665':
                    await message.channel.send(f'You\'re the best :heart_eyes:')
                else:
                    await message.channel.send(f'Kevin G is the best :heart_eyes:')

            elif message.content.lower().startswith('wish me luck'):
                if str(message.author) == 'bevin#2665':
                    await message.channel.send(f'Good luck bevin! :four_leaf_clover:')
                else:
                    await message.channel.send(f'I\'m okay, thanks. :rolling_eyes:')

            elif message.content.lower().startswith('/remaining'):
                # read in sheet responses in xlsx responses
                df = pd.read_excel('responses.xlsx', sheet_name='responses')

                # count number of teams where remaining is not 0
                remaining = len(df.loc[df['remaining'] != 0, 'remaining'].tolist())

                # send message with remaining
                await message.channel.send(f'There are {remaining} teams remaining.')

client.run(TOKEN)