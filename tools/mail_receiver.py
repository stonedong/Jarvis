import imaplib
import email
from email.header import decode_header
from config import settings
from utils import logger

class MailReceiver:
    """邮件接收工具，从IMAP服务器读取邮件"""
    
    def execute(self):
        """
        从收件箱中获取并读取未读邮件
        :return: 邮件列表，每封邮件包括发件人、主题和正文
        """
        # ----- 1. 获取IMAP配置 -----
        imap_host = settings.IMAP_HOST
        imap_port = settings.IMAP_PORT
        username = settings.SMTP_USER  # 可以和发件人地址相同
        password = settings.SMTP_PASSWORD

        # 必要配置校验
        if not all([imap_host, imap_port, username, password]):
            missing = []
            if not imap_host: missing.append(self.ENV_IMAP_HOST)
            if not imap_port: missing.append(self.ENV_IMAP_PORT)
            if not username: missing.append(self.ENV_SMTP_USER)
            if not password: missing.append(self.ENV_SMTP_PASSWORD)
            raise ValueError(f"缺少必要的IMAP环境变量: {', '.join(missing)}")

        # ----- 2. 连接到IMAP服务器 -----
        try:
            with imaplib.IMAP4_SSL(imap_host, int(imap_port)) as server:
                server.login(username, password)
                server.select('inbox')  # 选择收件箱

                # 搜索所有未读邮件
                status, messages = server.search(None, 'UNSEEN')  # 'ALL' 获取所有邮件，'UNSEEN' 获取未读邮件
                logger.info(f"received response from IMAP server: {messages}")
                logger.info(f"搜索邮件状态: {status}, 邮件数量: {len(messages[0].split()) if status == 'OK' else 0}")
                if status != 'OK':
                    raise ValueError("无法获取邮件列表")

                # 处理邮件
                mails = []
                for msg_num in messages[0].split():
                    # 获取邮件数据
                    status, msg_data = server.fetch(msg_num, '(RFC822)')
                    if status != 'OK':
                        logger.warning(f"无法获取邮件: {msg_num}")
                        continue

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # 获取发件人
                            from_header = msg.get("From")
                            subject, encoding = decode_header(msg.get("Subject"))[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding or 'utf-8')

                            # 获取邮件正文
                            body = None
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))
                                    
                                    # 如果是正文部分
                                    if content_type == "text/plain" and "attachment" not in content_disposition:
                                        body = part.get_payload(decode=True).decode()
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode()

                            # 添加邮件信息
                            mails.append({
                                'from': from_header,
                                'subject': subject,
                                'body': body
                            })

                    # 标记邮件为已读
                    server.store(msg_num, '+FLAGS', '\\Seen')
                    
                # 返回所有未读邮件
                logger.info(f"共读取到 {len(mails)} 封未读邮件")
                return mails

        except Exception as e:
            logger.error(f"读取邮件失败: {e}")
            raise ValueError(f"读取邮件失败: {e}")


if __name__ == "__main__":
    receiver = MailReceiver()
    mails = receiver.execute()
    for mail in mails:
        print(f"From: {mail['from']}")
        print(f"Subject: {mail['subject']}")
        print(f"Body: {mail['body']}")
        print("-" * 40)