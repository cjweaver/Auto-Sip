# Get the process metadata for a SIP


def getprocess_md(site, src_sip_id):
    src_url = "{0}/api/SIP/{1}".format(site, src_sip_id)
    print("getting information for sip", src_sip_id)
    src_req = requests.get(src_url, verify=False)
    src_json = src_req.json()
