TEMPLATE_XML = """<?xml version="1.0" encoding="iso-8859-2" ?>
<!DOCTYPE scenario SYSTEM "sipp.dtd">

<scenario name="Call with enabled profile and good credential 5calls x seconds max peak 300 simultaneous calls">

    <send retrans="500">
          <![CDATA[

                INVITE sip:[field3]@[remote_ip]:[remote_port] SIP/2.0
                Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
                From: sipp <sip:[field0]@[field1]>;tag=[call_number]
                To: <sip:[field3]@[field1]:[remote_port]>
                Call-ID: [call_id]
                CSeq: [cseq] INVITE
                Contact: sip:[field0]@[local_ip]:[local_port]
                Max-Forwards: 70
                Content-Type: application/sdp
                Content-Length: [len]

                v=0
                o=user1 53655765 2353687637 IN IP[local_ip_type] [local_ip]
                s=-
                c=IN IP[media_ip_type] [media_ip]
                t=0 0
                m=audio [media_port] RTP/AVP 8
                a=rtpmap:8 PCMA/8000

          ]]>
    </send>

    <recv response="100" optional="true"></recv>
    <recv response="407" auth="true" rrs="true"></recv>

    <send>
    <![CDATA[

          ACK sip:[field3]@[remote_ip]:[remote_port] SIP/2.0
          [last_Via:]
          [last_From:]
          [last_To:]
          [last_Call-ID:]
          CSeq: [cseq] ACK
          Contact: <sip:[local_ip]:[local_port];transport=[transport]>
          Max-Forwards: 60
          Content-Length: 0

    ]]>
    </send>


    <send retrans="500">
          <![CDATA[

                INVITE sip:[field3]@[remote_ip]:[remote_port] SIP/2.0
                Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
                From: sipp <sip:[field0]@[field1]>;tag=[pid]sippTag01[call_number]
                To: <sip:[field3]@[field1]:[remote_port]>
                Call-ID: [call_id]
                CSeq: [cseq] INVITE
                Contact: <sip:[local_ip]:[local_port];transport=[transport]>
                [field2]
                Max-Forwards: 50
                Content-Type: application/sdp
                Content-Length: [len]

                v=0
                o=user1 53655765 2353687637 IN IP[local_ip_type] [local_ip]
                s=-
                c=IN IP[media_ip_type] [media_ip]
                t=0 0
                m=audio [media_port] RTP/AVP 8
                a=rtpmap:8 PCMA/8000

          ]]>
    </send>

    <recv response="100" optional="true"></recv>
    <recv response="183" optional="true"></recv>
    <recv response="180" optional="true"></recv>
    <recv response="200" rrs="true"></recv>

    <send>
          <![CDATA[

          ACK [next_url] SIP/2.0
          [last_Via:]
          [routes]
          [last_From:]
          [last_To:]
          Call-ID: [call_id]
          CSeq: [cseq] ACK
          Contact: sip:[field0]@[local_ip]:[local_port]
          Max-Forwards: 40
          Content-Length: 0

          ]]>
    </send>

    <pause milliseconds="%(call_duration)d" />

    <send retrans="500">
          <![CDATA[

          BYE [next_url] SIP/2.0
          [last_Via:]
          [routes]
          [last_From:]
          [last_To:]
          [last_Call-ID:]
          CSeq: [cseq] BYE
          Contact: <sip:[local_ip]:[local_port];transport=[transport]>
          Max-Forwards: 30
          Content-Length: 0

          ]]>
    </send>

    <!-- The 'crlf' option inserts a blank line in the statistics report. -->
    <recv response="200" crlf="true">
    </recv>

    <!-- definition of the response time repartition table (unit is ms)       -->
    <ResponseTimeRepartition value="10, 20, 30, 40, 50, 100, 150, 200"/>

    <!-- definition of the call length repartition table (unit is ms)             -->
    <CallLengthRepartition value="10, 50, 100, 500, 1000, 5000, 10000"/>

</scenario>
"""
