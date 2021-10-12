template_add_contact = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><msg serviceID="14" templateID="1" action="plugin" actionData="AppCmd://OpenContactInfo/?uin={uin}" a_actionData="mqqapi://card/show_pslcard?src_type=internal&amp;source=sharecard&amp;version=1&amp;uin={uin}" i_actionData="mqqapi://card/show_pslcard?src_type=internal&amp;source=sharecard&amp;version=1&amp;uin={uin}" brief="{brief}" sourceMsgId="0" url="" flag="1" adverSign="0" multiMsgFlag="0"><item layout="0" mode="1" advertiser_id="0" aid="0"><summary>{summary}</summary><hr hidden="false" style="0"/></item><item layout="2" mode="1" advertiser_id="0" aid="0"><picture cover="mqqapi://card/show_pslcard?src_type=internal&amp;source=sharecard&amp;version=1&amp;uin={uin}" w="0" h="0"/><title>{title}</title><summary>{detail}</summary></item><source name="" icon="" action="" appid="-1"/></msg>"""


def contact(qq: int, title: str, subtitle: str, detail: str, brief="推荐联系人") -> str:
    return template_add_contact.format(
        uin=qq,
        summary=title,
        title=subtitle,
        detail=detail,
        brief=brief
    )
