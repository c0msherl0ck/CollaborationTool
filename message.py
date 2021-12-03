import os
import re
import binascii
import csv
import argparse
import datetime

def convert_datetime(unixtime):
    """Convert unixtime to datetime"""
    date = datetime.datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')
    return date # format : str

def remove_abnormal_characters(Str):
    """cp949로 표현할 수 없는 쓰레기 문자를 필터링 하는 과정"""
    Str = Str.encode('cp949', 'ignore').decode('cp949')
    return Str

def refining(txt):
    """문자열을 정제하며 \w(알파벳, 숫자, _)와 특수문자(-:.)만을 남긴다."""
    txt = re.sub('[^\w\-\:\.]', '', txt)
    return txt

def decoding(bStr):
    """영문은 ascii, 한글은 utf-16으로 디코딩하여 변환한다."""
    # 함수 인자를 넘겨 받을 때 스트링 형식으로 받으므로, 헥사 값으로 변환 필요
    hexStr = str(binascii.hexlify(bStr), 'ascii').upper()
    decoded_text = ''

    if hexStr[0:2] == '22':
        bcontent = binascii.a2b_hex(hexStr[4:])  # 22 \w\w 제거
        decoded_text = bcontent.decode('ascii', 'ignore')
    else:
        try:
            bcontent = binascii.a2b_hex(hexStr[4:])
            decoded_text = bcontent.decode('utf-16')
        except UnicodeDecodeError as e:
            bcontent = binascii.a2b_hex(hexStr[6:])
            decoded_text = bcontent.decode('utf-16')
    return decoded_text

def parse_slack_team_info(hexString, wr):
    # team attribute array
    # 팀 속성 중 중요 속성 5개에 대해서만 탐색
    team_attribute_bText_array = [b'id',
                                    b'name',
                                    b'email_domain',
                                    b'domain',
                                    b'msg_edit_window_mins'
                                    ]
    team_attribute_hex_array = []
    for attr in team_attribute_bText_array:
        attr_hex = str(binascii.hexlify(attr), 'ascii')
        attr_hex = str(attr_hex).upper()  # make a-z to A-Z
        team_attribute_hex_array.append(attr_hex)

    # 각 속성 앞에는 ". 라는 문자가 존재하므로 속성 앞에 해당 문자열을 추가한다.
    # 헥사값 22\w\w 는 정규표현식으로 ". 문자에 해당한다.
    for i in range(0, len(team_attribute_hex_array)):
        team_attribute_hex_array[i] = '22\\w\\w' + team_attribute_hex_array[i]

    # 헥사값으로 이루어진 패턴을 만든다.
    # 단, 데이터 길이의 최대값을 정해둔다.
    team_pattern_hex = ''
    for i in range(0, len(team_attribute_hex_array)):
        attr_hex = team_attribute_hex_array[i]
        if i != len(team_attribute_hex_array) - 1:
            team_pattern_hex = team_pattern_hex + attr_hex + '(.{1,100}?)'
        else:
            team_pattern_hex = team_pattern_hex + attr_hex

    # Searching File Data using Regular Expression
    team_pattern_RegExr = re.compile(team_pattern_hex)

    print('\nSearching team info...')
    teams = team_pattern_RegExr.findall(hexString)
    print('# of teams : ' + str(len(teams)))

    # Parsing teams
    if len(teams) != 0:
        print('\nParsing teams...')
        # 첫 행 이름에 id, name 컬럼명을 적는다.
        wr.writerow(['team_id',  # 0
                     'team_name'  # 1
                     ])
        for team in teams:
            print(' *** Raw Data *** ')
            for i in range(0, len(team)):
                if i in [0, 1]:
                    print('team' + '[' + str(i) + ']' + '\t' + str(len(team[i])) + '\t' + str(team[i]))
            print()

            try:
                bid = binascii.a2b_hex(team[0]) # 팀 고유 식별자
                bname = binascii.a2b_hex(team[1]) # 팀 이름

                strid = bid.decode('ascii', 'ignore')
                # text 속성에 해당하는 값은 영문 ascii 한글 utf-16 디코딩하여 별도 처리
                strname = decoding(bname)

                # refining() 함수를 이용한 문자열 정제 과정
                strid = refining(strid)
                # text 속성에서 cp949로 표현할 수 없는 문자 또한 제거한다.
                strname = remove_abnormal_characters(strname)

                print('member_id: ' + strid)
                print('member_name: ' + strname)

                wr.writerow([strid,
                             strname,
                             ])
            except Exception as e:
                print(str(e))
        # === End of For 문 ===
        print('*** End of Team Information ***')
        wr.writerow([''])
    else:
        print('Can not find team information..')


def parse_slack_member_info(hexString, wr):
    # member attribute array
    # 멤버 속성 중 중요 속성 10개에 대해서만 탐색
    member_attribute_bText_array = [b'files',
                                    b'activity',
                                    b'stars',
                                    b'mentions',
                                    b'id',
                                    b'team_id',
                                    b'name',
                                    b'deleted',
                                    b'color',
                                    b'real_name',
                                    b'tz',
                                    ]
    member_attribute_hex_array = []
    for attr in member_attribute_bText_array:
        attr_hex = str(binascii.hexlify(attr), 'ascii')
        attr_hex = str(attr_hex).upper()  # make a-z to A-Z
        member_attribute_hex_array.append(attr_hex)

    # 각 속성 앞에는 ". 라는 문자가 존재하므로 속성 앞에 해당 문자열을 추가한다.
    # 헥사값 22\w\w 는 정규표현식으로 ". 문자에 해당한다.
    for i in range(0, len(member_attribute_hex_array)):
        member_attribute_hex_array[i] = '22\\w\\w' + member_attribute_hex_array[i]

    # 헥사값으로 이루어진 패턴을 만든다.
    # 단, 데이터 길이의 최대값을 정해둔다.
    member_pattern_hex = ''
    for i in range(0, len(member_attribute_hex_array)):
        attr_hex = member_attribute_hex_array[i]
        if i != len(member_attribute_hex_array) - 1:
            member_pattern_hex = member_pattern_hex + attr_hex + '(.{1,100}?)'
        else:
            member_pattern_hex = member_pattern_hex + attr_hex

    # Searching File Data using Regular Expression
    member_pattern_RegExr = re.compile(member_pattern_hex)

    print('\nSearching members...')
    members = member_pattern_RegExr.findall(hexString)
    print('# of members : ' + str(len(members)))

    # Parsing members
    if len(members) != 0:
        print('\nParsing members...')
        # 첫 행 이름에 id, name , real_name 컬럼명을 적는다.
        wr.writerow(['member_id',  # 4
                     'member_name',  # 6
                     'member_real_name' # 9
                     ])
        for member in members:
            print(' *** Raw Data *** ')
            for i in range(0, len(member)):
                if i in [4, 6, 9]:
                    print('member' + '[' + str(i) + ']' + '\t' + str(len(member[i])) + '\t' + str(member[i]))
            print()

            try:
                bid = binascii.a2b_hex(member[4]) # 사용자 고유 식별자
                bname = binascii.a2b_hex(member[6]) # 사용자 ID
                breal_name = binascii.a2b_hex(member[9]) # 사용자 이름

                strid = bid.decode('ascii', 'ignore')
                strname = bname.decode('ascii', 'ignore')
                # text 속성에 해당하는 값은 영문 ascii 한글 utf-16 디코딩하여 별도 처리
                strreal_name = decoding(breal_name)

                # refining() 함수를 이용한 문자열 정제 과정
                strid = refining(strid)
                strname = refining(strname)
                # text 속성에서 cp949로 표현할 수 없는 문자 또한 제거한다.
                strreal_name = remove_abnormal_characters(strreal_name)

                print('member_id: ' + strid)
                print('member_name: ' + strname)
                print('member_real_name: ' + strreal_name)

                wr.writerow([strid,
                             strname,
                             strreal_name
                             ])
            except Exception as e:
                print(str(e))
            print('===========')
        # === End of For 문 ===
        print('*** End of Member Information ***')
        wr.writerow([''])
    else:
        print('Can not find member information')

def parse_slack_channel_info(hexString, wr):
    # channel attribute array
    # 채널 속성 중 중요 속성 10개에 대해서만 탐색
    channel_attribute_bText_array = [b'id',
                                    b'name',
                                    b'is_channel',
                                    b'is_group',
                                    b'is_im',
                                    b'created',
                                    b'is_archived',
                                    b'is_general',
                                    b'unlinked',
                                    b'name_normalized',
                                    b'is_frozen'
                                    ]
    channel_attribute_hex_array = []
    for attr in channel_attribute_bText_array:
        attr_hex = str(binascii.hexlify(attr), 'ascii')
        attr_hex = str(attr_hex).upper()  # make a-z to A-Z
        channel_attribute_hex_array.append(attr_hex)

    # 각 속성 앞에는 ". 라는 문자가 존재하므로 속성 앞에 해당 문자열을 추가한다.
    # 헥사값 22\w\w 는 정규표현식으로 ". 문자에 해당한다.
    for i in range(0, len(channel_attribute_hex_array)):
        channel_attribute_hex_array[i] = '22\\w\\w' + channel_attribute_hex_array[i]

    # 헥사값으로 이루어진 패턴을 만든다.
    # 단, 데이터의 최대값을 정해둔다.
    channel_pattern_hex = ''
    for i in range(0, len(channel_attribute_hex_array)):
        attr_hex = channel_attribute_hex_array[i]
        if i != len(channel_attribute_hex_array) - 1:
            channel_pattern_hex = channel_pattern_hex + attr_hex + '(.{1,100}?)'
        else:
            channel_pattern_hex = channel_pattern_hex + attr_hex

    # Searching File Data using Regular Expression
    channel_pattern_RegExr = re.compile(channel_pattern_hex)

    print('\nSearching channels...')
    channels = channel_pattern_RegExr.findall(hexString)
    print('# of channels : ' + str(len(channels)))

    # Parsing Files
    if len(channels) != 0:
        print('\nParsing channels...')
        # 첫 행 이름에 id, name 컬럼명을 적는다.
        wr.writerow(['channel_id',  # 0
                     'channel_name',  # 1
                     ])
        for channel in channels:
            print(' *** Raw Data *** ')
            for i in range(0, len(channel)):
                if i in [0, 1]:
                    print('channel' + '[' + str(i) + ']' + '\t' + str(len(channel[i])) + '\t' + str(channel[i]))
            print()

            try:
                bid = binascii.a2b_hex(channel[0]) # 채널 고유 식별자
                bname = binascii.a2b_hex(channel[1]) # 채널 이름

                strid = bid.decode('ascii', 'ignore')
                # text 속성에 해당하는 값은 영문 ascii 한글 utf-16 디코딩하여 별도 처리
                strname = decoding(bname)

                # refining() 함수를 이용한 문자열 정제 과정
                strid = refining(strid)
                # text 속성에서 cp949로 표현할 수 없는 문자 또한 제거한다.
                strname = remove_abnormal_characters(strname)

                print('channel_id: ' + strid)
                print('channel_name: ' + strname)

                wr.writerow([strid,
                             strname,
                             ])
            except Exception as e:
                print(str(e))
            print('===========')
        # === End of For 문 ===
        print('*** End of Channel Information ***')
        wr.writerow([''])
    else:
        print('Can not find channel information')

def parse_slack_files(hexString, wr):
    # file attribute array
    # 파일 속성 중 중요 속성 6개에 대해서만 탐색
    file_attribute_bText_array = [b'comments',
                                    b'ims',
                                    b'groups',
                                    b'id',
                                    b'is_tombstoned',
                                    b'name',
                                    b'title']
    file_attribute_hex_array = []
    for attr in file_attribute_bText_array:
        attr_hex = str(binascii.hexlify(attr), 'ascii')
        attr_hex = str(attr_hex).upper()  # make a-z to A-Z
        file_attribute_hex_array.append(attr_hex)

    # 각 속성 앞에는 ". 라는 문자가 존재하므로 속성 앞에 해당 문자열을 추가한다.
    # 헥사값 22\w\w 는 정규표현식으로 ". 문자에 해당한다.
    for i in range(0, len(file_attribute_hex_array)):
        file_attribute_hex_array[i] = '22\\w\\w' + file_attribute_hex_array[i]

    # 헥사값으로 이루어진 패턴을 만든다.
    # 단, 데이터 길이의 최대값을 정해둔다.
    file_pattern_hex = ''
    for i in range(0, len(file_attribute_hex_array)):
        attr_hex = file_attribute_hex_array[i]
        if i != len(file_attribute_hex_array) - 1:
            file_pattern_hex = file_pattern_hex + attr_hex + '(.{1,100}?)'
        else:
            file_pattern_hex = file_pattern_hex + attr_hex

    # Searching File Data using Regular Expression
    file_pattern_RegExr = re.compile(file_pattern_hex)

    print('\nSearching files...')
    files = file_pattern_RegExr.findall(hexString)
    print('# of files : ' + str(len(files)))

    # Parsing Files
    if len(files) != 0:
        print('\nParsing files...')
        # 첫 행 이름에 id, name 컬럼명을 적는다.
        wr.writerow(['file_id',  # 3
                     'file_name',  # 5
                     ])
        for file in files:
            print(' *** Raw Data *** ')
            for i in range(0, len(file)):
                if i in [3, 5]:
                    print('message' + '[' + str(i) + ']' + '\t' + str(len(file[i])) + '\t' + str(file[i]))
            print()

            try:
                bid = binascii.a2b_hex(file[3]) # 파일 고유 식별자
                bname = binascii.a2b_hex(file[5]) # 파일명

                strid = bid.decode('ascii', 'ignore')
                # text 속성에 해당하는 값은 영문 ascii 한글 utf-16 디코딩하여 별도 처리
                strname = decoding(bname)

                # refining() 함수를 이용한 문자열 정제 과정
                strid = refining(strid)
                # text 속성에서 cp949로 표현할 수 없는 문자 또한 제거한다.
                strname = remove_abnormal_characters(strname)

                print('file_id: ' + strid)
                print('file_name: ' + strname)

                wr.writerow([strid,
                             strname,
                             ])
            except Exception as e:
                print(str(e))
            print('===========')
        # === End of For 문 ===
        print('*** End of Files ***')
        wr.writerow([''])
    else:
        print('Can not find file info..')

def parse_slack_messages(hexString, wr):

    # message attribute array
    # 메시지 속성 중 client_msg_id를 제외한 20개의 속성으로 패턴 검색을 진행한다.
    message_attribute_bText_array = [b'thread_ts',
                                    b'slackbot_feels',
                                    b'_hidden_reply',
                                    b'reply_count',
                                    b'replies',
                                    b'latest_reply',
                                    b'reply_users',
                                    b'reply_users_count',
                                    b'files',
                                    b'attachments',
                                    b'blocks',
                                    b'type',
                                    b'ts',
                                    b'channel',
                                    b'no_display',
                                    b'user',
                                    b'_rxn_key',
                                    b'subtype',
                                    b'text',
                                    b'__meta__'
                                    ]
    message_attribute_hex_array = []
    for attr in message_attribute_bText_array:
        attr_hex = str(binascii.hexlify(attr), 'ascii')
        attr_hex = str(attr_hex).upper()  # make a-z to A-Z
        message_attribute_hex_array.append(attr_hex)

    # 각 속성 앞에는 ". 라는 문자가 존재하므로 속성 앞에 해당 문자열을 추가한다.
    # 헥사값 22\w\w 는 정규표현식으로 ". 문자에 해당한다.
    for i in range(0, len(message_attribute_hex_array)):
        message_attribute_hex_array[i] = '22\\w\\w' + message_attribute_hex_array[i]

    # 헥사값으로 이루어진 패턴을 만든다.
    message_pattern_hex = ''
    for i in range(0, len(message_attribute_hex_array)):
        attr_hex = message_attribute_hex_array[i]
        if i != len(message_attribute_hex_array) - 1:
            message_pattern_hex = message_pattern_hex + attr_hex + '(.+?)'
        else:
            message_pattern_hex = message_pattern_hex + attr_hex

    # Searching Message Data using Regular Expression
    message_pattern_RegExr = re.compile(message_pattern_hex)

    print('\nSearching messages...')
    messages = message_pattern_RegExr.findall(hexString)
    print('# of messages : ' + str(len(messages)))

    # Parsing Messages
    if len(messages) != 0:
        print('\nParsing messages...')
        # 주요 속성명 10개
        wr.writerow(['thread_ts',  # 0
                     'files',  # 8
                     'ts',  # 12
                     'channel',  # 13
                     'user',  # 15
                     'text',  # 18
                     'time' # ts 속성에 unix timestamp 형태로 저장된 데이터를 date 형태로 변환한 값
                     ])
        for message in messages:
            print(' *** Raw Data *** ')
            for i in range(0, len(message)):
                if i in [0, 8, 12, 13, 15, 18]:
                    print('message' + '[' + str(i) + ']' + '\t' + str(len(message[i])) + '\t' + str(message[i]))
            print()

            try:
                bthread_ts = binascii.a2b_hex(message[0])
                bfiles = binascii.a2b_hex(message[8])
                bts = binascii.a2b_hex(message[12])
                bchannel = binascii.a2b_hex(message[13])
                buser = binascii.a2b_hex(message[15])
                btext = binascii.a2b_hex(message[18])

                strthread_ts = bthread_ts.decode('ascii', 'ignore')
                strfiles = bfiles.decode('ascii', 'ignore')
                strts = bts.decode('ascii', 'ignore')
                strchannel = bchannel.decode('ascii', 'ignore')
                struser = buser.decode('ascii', 'ignore')
                # text 속성에 해당하는 값은 영문 ascii 한글 utf-16 디코딩하여 별도 처리
                strtext = decoding(btext)

                # refining() 함수를 이용한 문자열 정제 과정
                strthread_ts = refining(strthread_ts)
                strfiles = refining(strfiles)
                strts = refining(strts)
                strchannel = refining(strchannel)
                struser = refining(struser)
                # text 속성에서 cp949로 표현할 수 없는 문자 또한 제거한다.
                strtext = remove_abnormal_characters(strtext)

                print('thread_ts: ' + strthread_ts)
                print('files: ' + strfiles[2:]) # "al" 문자열 제거
                print('ts: ' + strts)
                print('channel: ' + strchannel)
                print('user: ' + struser)
                print('text: ' + strtext)
                print('time: ' + str(convert_datetime(float(strts))))

                wr.writerow([strthread_ts,
                            strfiles[2:],
                            strts,
                            strchannel,
                            struser,
                            strtext,
                            str(convert_datetime(float(strts)))
                            ])
            except Exception as e:
                print(str(e))
            print('===========')
        # === End of For 문 ===
        print('# of messages : ' + str(len(messages)))
    else:
        print('There is no message..')

def extract_data_from_slack(fileName):
    print('\n'+'Extract data from slack indexedDB : '+fileName+'\n')
    with open(fileName, 'rb') as input, open(fileName+'.csv', 'w', newline='') as output:
        # csv writer
        wr = csv.writer(output)
        # Read Binary Data as Hex Value
        data = input.read()
        # bString = str(data) # decode by ascii table
        hexData = binascii.b2a_hex(data) # binary i/o ascii to hex
        hexString = str(hexData).upper() # make a-z to A-Z

        # RegExr Pattern Matching
        parse_slack_team_info(hexString, wr)
        parse_slack_member_info(hexString, wr)
        parse_slack_channel_info(hexString, wr)
        parse_slack_files(hexString, wr)
        parse_slack_messages(hexString, wr)

def process_teams_attachment(bStr):
    """첨부파일 속성에 해당하는 데이터를 넘겨받아 첨부파일 하위 속성으로 재해석한 결과(첨부파일명)를 배열로 반환한다."""
    # 함수 인자를 넘겨 받을 때 스트링 형식으로 받으므로 헥사 값으로 변환이 필요하다.
    # 또한, 문자열 매칭은 영문 대문자를 기준으로 진행한다.
    hexStr = str(binascii.hexlify(bStr), 'ascii').upper()

    # attachment attribute array
    # 메시지 속성은 총 16개가 존재
    attachment_attribute_bText_array = [b'objectId',
                                        b'itemId',
                                        b'title',
                                        b'type'
                                        ]
    attachment_attribute_hex_array = []
    for attr in attachment_attribute_bText_array:
        attr_hex = str(binascii.hexlify(attr), 'ascii')
        attr_hex = str(attr_hex).upper()  # make a-z to A-Z
        attachment_attribute_hex_array.append(attr_hex)

    # 각 속성 앞에는 ". 라는 문자가 존재하므로 속성 앞에 해당 문자열을 추가한다.
    # 헥사값 22\w\w 는 정규표현식으로 ". 문자에 해당한다.
    for i in range(0,len(attachment_attribute_hex_array)):
        attachment_attribute_hex_array[i] = '22\\w\\w'+attachment_attribute_hex_array[i]

    # 헥사값으로 이루어진 패턴을 만든다.
    attachment_pattern_hex = ''
    for i in range(0, len(attachment_attribute_hex_array)):
        attr_hex = attachment_attribute_hex_array[i]
        if i != len(attachment_attribute_hex_array) - 1:
            attachment_pattern_hex = attachment_pattern_hex + attr_hex + '(.+?)'
        else:
            attachment_pattern_hex = attachment_pattern_hex + attr_hex

    # Searching Attribute Data using Regular Expression
    attachment_pattern_RegExr = re.compile(attachment_pattern_hex)

    print('\n Interpreting attachment information...')
    attachments = attachment_pattern_RegExr.findall(hexStr)
    print('# of attachments : ' + str(len(attachments)))
    print()
    # 첨부파일의 속성 중 첨부파일명에 해당하는 하위 속성 title 속성을 배열로 반환한다.
    attachment_title_array = []
    for attachment in attachments:
        print(' *** Attachment Raw Data *** ')
        for i in range(0, len(attachment)):
            if i in [2]: # title 속성에 대해서만 추출한다. 나머지 속성의 값은 유의미한 값을 지니지 않는다.
                print('attribute' + '[' + str(i) + ']' + '\t' + str(len(attachment[i])) + '\t' + str(attachment[i]))
        try:
            btitle = binascii.a2b_hex(attachment[2])
            strtitle = decoding(btitle)  # 영문 ascii 한글 utf-16 디코딩하여 별도 처리
            attachment_title_array.append(strtitle)
            print('attachment title: ' + strtitle)
            print()
        except Exception as e:
            print(str(e))
    # end of for 문
    return attachment_title_array

def extract_data_from_teams(fileName):
    print('\n' + 'Extract data from Microsoft Teams indexedDB : ' + fileName + '\n')
    with open(fileName, 'rb') as input, open(fileName + '.csv', 'w', newline='') as output:
        # csv writer
        wr = csv.writer(output)

        # Read Binary Data as Hex Value
        data = input.read()
        hexData = binascii.b2a_hex(data)  # binary i/o ascii to hex
        hexString = str(hexData).upper()  # make a-z to A-Z

        # Message Attribute Array
        # 메시지 속성은 총 99개가 존재
        message_attribute_bText_array = [b'ackrequired',
                                        b'versionHistory',
                                        b'cursorToken',
                                        b'messagetype',
                                        b'contenttype',
                                        b'content',
                                        b'renderContent',
                                        b'renderContentNative',
                                        b'activitytype',
                                        b'clientmessageid',
                                        b'amsreferences',
                                        b'amsStorageLocations',
                                        b'isAmsResourcesUpdated',
                                        b'imdisplayname',
                                        b'skypeguid',
                                        b'postChannels',
                                        b'properties',
                                        b'annotationsSummary',
                                        b'externalid',
                                        b'id',
                                        b'type',
                                        b'sequenceId',
                                        b'messageKind',
                                        b'composetime',
                                        b'originalarrivaltime',
                                        b'clientArrivalTime',
                                        b'conversationLink',
                                        b'from',
                                        b'source',
                                        b'idUnion',
                                        b'conversationId',
                                        b'versionNumber',
                                        b'version',
                                        b'messageStorageState',
                                        b'isActionExecuteUpdate',
                                        b'_conversationIdMessageIdUnion',
                                        b'parentMessageId',
                                        b'createdTime',
                                        b'creator',
                                        b'creatorProfile',
                                        b'isFromMe',
                                        b'userHasStarred',
                                        b'activity',
                                        b'previewData',
                                        b'replyChainLatestDeliveryTime',
                                        b'scenarioName',
                                        b'state',
                                        b'hydratedContent',
                                        b'hydratedProperties',
                                        b'notificationLevel',
                                        b'hasMessageActionFailed',
                                        b'messageSendErrorReason',
                                        b'messageSendDiagnosticError',
                                        b'mentions',
                                        b'hyperLinks',
                                        b'attachments',
                                        b'inputExtensionAttachments',
                                        b'processedInputExtensionAttachments',
                                        b'inlineImages',
                                        b'containsSelfMention',
                                        b'containsTeamMention',
                                        b'teamMentionDisplayName',
                                        b'trimmedMessageContent',
                                        b'messageContentContainsImage',
                                        b'messageContentContainsVideo',
                                        b'isSanitized',
                                        b'isPlainTextConvertedToHtml',
                                        b'isRichContentProcessed',
                                        b'isRichMessagePropertiesProcessed',
                                        b'isRenderContentWithGiphyDisplayEnabled',
                                        b'isForceDelete',
                                        b'isEditClientLie',
                                        b'reactionLieData',
                                        b'originalNonLieMessage',
                                        b'originalNonLieReactions',
                                        b'originalNonLieReactionsSummary',
                                        b'context',
                                        b'isSfBGroupConversation',
                                        b'convoCallId',
                                        b'convoCallUrl',
                                        b'eventId',
                                        b'translation',
                                        b'dlpData',
                                        b'layoutMetadata',
                                        b'messageLayoutType',
                                        b'callDuration',
                                        b'callParticipantsMris',
                                        b'cachedDeduplicationKey',
                                        b'cachedOriginalArrivalTime',
                                        b'cachedOriginalArrivalTimeUtc',
                                        b'_emailDetails',
                                        b'_callRecording',
                                        b'_callTranscript',
                                        b'_meetingObjects',
                                        b'callParticipantsCount',
                                        b'_pinState',
                                        b'pinnedTime',
                                        b'_policyViolation',
                                        b'_invalidateInvokeCacheDetails'
                                        ]
        message_attribute_hex_array = []
        for attr in message_attribute_bText_array:
            attr_hex = str(binascii.hexlify(attr), 'ascii')
            attr_hex = str(attr_hex).upper() # make a-z to A-Z
            message_attribute_hex_array.append(attr_hex)

        # 각 속성 앞에는 ". 라는 문자가 존재하므로 속성 앞에 해당 문자열을 추가한다.
        # 헥사값 22\w\w 는 정규표현식으로 ". 문자에 해당한다.
        for i in range(0,len(message_attribute_hex_array)):
            message_attribute_hex_array[i] = '22\\w\\w'+message_attribute_hex_array[i]

        # 헥사값으로 이루어진 패턴을 만든다.
        message_pattern_hex = ''
        for i in range(0,len(message_attribute_hex_array)):
            attr_hex = message_attribute_hex_array[i]
            if i != len(message_attribute_hex_array)-1:
                message_pattern_hex = message_pattern_hex + attr_hex + '(.+?)'
            else:
                message_pattern_hex = message_pattern_hex + attr_hex

        # Searching Message Data using Regular Expression
        message_pattern_RegExr = re.compile(message_pattern_hex)

        print('\nSearching messages...')
        messages = message_pattern_RegExr.findall(hexString)
        print('# of messages : ' + str(len(messages)))

        # Parsing Messages
        if len(messages) != 0:
            print('\nParsing messages...')
            # 주요 속성명 10개
            wr.writerow(['content', #5
                         'clientmessageid', #9
                         'imdisplayname', #13
                         'composetime', #23
                         'originalarrivaltime', #24
                         'clientArrivalTime', #25
                         'conversationId', #30
                         'parentMessageId', #36
                         'creator', #38
                         'attachments', #55
                         ])
            for message in messages:
                print(' *** Raw Data *** ')
                for i in range(0,len(message)):
                    if i in [5, 9, 13, 23, 24, 25, 30, 36, 38, 55]:
                        print('message'+'['+str(i)+']'+'\t'+str(len(message[i]))+'\t'+str(message[i]))
                print()

                try:
                    bcontent = binascii.a2b_hex(message[5])
                    bclientmessageid = binascii.a2b_hex(message[9])
                    bimdisplayname = binascii.a2b_hex(message[13])
                    bcomposetime = binascii.a2b_hex(message[23])
                    boriginalarrivaltime = binascii.a2b_hex(message[24])
                    bclientArrivalTime = binascii.a2b_hex(message[25])
                    bconversationId = binascii.a2b_hex(message[30])
                    bparentMessageId = binascii.a2b_hex(message[36])
                    bcreator = binascii.a2b_hex(message[38])
                    battachments = binascii.a2b_hex(message[55])

                    # content 속성에 해당하는 값은 영문 ascii 한글 utf-16 디코딩하여 별도 처리
                    strcontent = decoding(bcontent)
                    strclientmessageid = bclientmessageid.decode('ascii', 'ignore')
                    # imdisplayname 속성에 해당하는 값은 ascii 한글 utf-16 디코딩하여 별도 처리
                    strimdisplayname = decoding(bimdisplayname)
                    strcomposetime = bcomposetime.decode('ascii', 'ignore')
                    stroriginalarrivaltime = boriginalarrivaltime.decode('ascii', 'ignore')
                    strclientArrivalTime = bclientArrivalTime.decode('ascii', 'ignore')
                    strconversationId = bconversationId.decode('ascii', 'ignore')
                    strparentMessageId = bparentMessageId.decode('ascii', 'ignore')
                    strcreator = bcreator.decode('ascii', 'ignore')
                    # 하위 속성에 따라 재해석하여 첨부파일명을 배열로 반환한다.
                    attachmentsArr = process_teams_attachment(battachments)
                    strattachments = ''
                    if len(attachmentsArr) != 0: # 첨부파일이 존재하면 각 첨부파일명을 이어 붙인다.
                        for attachment in attachmentsArr:
                            strattachments = strattachments + str(attachment)

                    # 문자열 정제 과정
                    strclientmessageid = refining(strclientmessageid)
                    strcomposetime = refining(strcomposetime)
                    stroriginalarrivaltime = refining(stroriginalarrivaltime)
                    strclientArrivalTime = refining(strclientArrivalTime)
                    strconversationId = refining(strconversationId)
                    strparentMessageId = refining(strparentMessageId)
                    strcreator = refining(strcreator)

                    print('content: '+strcontent)
                    print('clientmessageid: '+strclientmessageid)
                    print('imdisplayname: '+strimdisplayname)
                    print('composetime: '+strcomposetime)
                    print('originalarrivaltime: '+stroriginalarrivaltime)
                    print('clientArrivalTime: '+strclientArrivalTime)
                    print('conversationId: '+strconversationId)
                    print('parentMessageId: '+strparentMessageId)
                    print('creator: '+strcreator)
                    print('attachments: '+strattachments)

                    wr.writerow([strcontent,
                                strclientmessageid,
                                strimdisplayname,
                                strcomposetime,
                                stroriginalarrivaltime,
                                strclientArrivalTime,
                                strconversationId,
                                strparentMessageId,
                                strcreator,
                                strattachments,
                                ])
                except Exception as e:
                    print(str(e))
                print('===========')
            # === End of For 문 ===
            print('# of messages : ' + str(len(messages)))
        else:
            print('There is no message..')

def is_valid_path(path):
    """
    Validates the path inputted and checks whether it is a file path or a folder path
    """
    if not path:
        raise ValueError(f"Invalid Path")
    if os.path.isfile(path):
        return path
    elif os.path.isdir(path):
        raise ValueError(f"{path} is a directory, please input a file")
    else:
        raise ValueError(f"Invalid Path {path}")

def parse_args():
    """
    Get user command line parameters
    """
    parser = argparse.ArgumentParser(description="Available Options")
    parser.add_argument('-i', '--input_path', dest='input_path', type=is_valid_path,
                        required=True, help="Enter the path of the file or the folder to process")
    parser.add_argument('-m', '--mode', dest='mode', choices=['slack', 'teams'], type=str,
                        default='RAM', help="Choose whether to process on Slack or Microsoft Teams")

    path = parser.parse_known_args()[0].input_path
    if os.path.isfile(path):
        parser.add_argument('-o', '--output_file', dest='output_file',
                            type=str, help="Enter a valid output file")

    # To Parse The Command Line Arguments
    args = vars(parser.parse_args())
    # To Display The Command Line Arguments
    print("## Command Arguments #################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in args.items()))
    print("######################################################################")
    return args

if __name__ == '__main__':
    # Parsing command line arguments entered by user
    args = parse_args()
    # Check if input is file
    input_file = is_valid_path(args['input_path'])
    mode = args['mode']
    if mode == 'slack':
        extract_data_from_slack(input_file)
    elif mode == 'teams':
        extract_data_from_teams(input_file)
    else:
        print('Wrong Choice..')
