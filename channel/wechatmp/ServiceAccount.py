import web
import time
import channel.wechatmp.reply as reply
import channel.wechatmp.receive as receive
from config import conf
from common.log import logger
from bridge.context import *
from channel.wechatmp.common import * 
from channel.wechatmp.wechatmp_channel import WechatMPChannel

# This class is instantiated once per query
class Query():

    def GET(self):
        return verify_server(web.input())

    def POST(self):
        # Make sure to return the instance that first created, @singleton will do that. 
        channel_instance = WechatMPChannel()
        try:
            webData = web.data()
            # logger.debug("[wechatmp] Receive request:\n" + webData.decode("utf-8"))
            wechatmp_msg = receive.parse_xml(webData)
            if wechatmp_msg.msg_type == 'text':
                from_user = wechatmp_msg.from_user_id
                message = wechatmp_msg.content.decode("utf-8")
                message_id = wechatmp_msg.msg_id

                logger.info("[wechatmp] {}:{} Receive post query {} {}: {}".format(web.ctx.env.get('REMOTE_ADDR'), web.ctx.env.get('REMOTE_PORT'), from_user, message_id, message))
                context = channel_instance._compose_context(ContextType.TEXT, message, isgroup=False, msg=wechatmp_msg)
                if context:
                    # set private openai_api_key
                    # if from_user is not changed in itchat, this can be placed at chat_channel
                    user_data = conf().get_user_data(from_user)
                    context['openai_api_key'] = user_data.get('openai_api_key') # None or user openai_api_key
                    channel_instance.produce(context)
                # The reply will be sent by channel_instance.send() in another thread
                return "success"

            elif wechatmp_msg.msg_type == 'event':
                logger.info("[wechatmp] Event {} from {}".format(wechatmp_msg.Event, wechatmp_msg.from_user_id))
                content = subscribe_msg()
                replyMsg = reply.TextMsg(wechatmp_msg.from_user_id, wechatmp_msg.to_user_id, content)
                return replyMsg.send()
            else:
                logger.info("暂且不处理")
                return "success"
        except Exception as exc:
            logger.exception(exc)
            return exc

