#!/usr/bin/python

import os
import json

dest_prefix = 'snippets-generated'
if not os.path.exists (dest_prefix):
    os.makedirs (dest_prefix)

f = open ('CloudFormationResourceSpecification.json', 'r')
spec = json.load (f)

rsrc_types = spec['ResourceTypes']
prop_types = spec['PropertyTypes']

snippets = {}

for key in prop_types.keys ():
    try:
        if "::" in key and "." in key:
            prop_name = key.split ('::')[2]
            primary_name = prop_name.split ('.')[1].lower ()
            qualifier = prop_name.split ('.')[0].lower ()
        else:
            primary_name = key.lower ()
            qualifier = None
    except:
        print "Error parsing property name: {0}".format (key)
        continue

    snippet_name = "{0}".format (primary_name)
    if snippet_name in snippets:
        if snippets[snippet_name] is not None:
            snip_rec = snippets[snippet_name]
            snippets["{1}-{0}".format (snip_rec['primary'], snip_rec['qualifier'])] = snip_rec
            snippets[snippet_name] = None

        snippet_name = "{1}-{0}".format (primary_name, qualifier)
        if snippet_name in snippets:
            print "Collision on property name {0}".format (snippet_name)

        snippets[snippet_name] = {'primary': primary_name, 'qualifier': qualifier, 'full_name': key, 'spec': prop_types[key]}

# go through and extract unique names for all resource types
for key in rsrc_types.keys ():
    primary_name = key.split ('::')[2].lower ()
    qualifier = key.split ('::')[1].lower ()

    snippet_name = "{0}".format (primary_name)
    # if the name has been seen before then store both the old and new name under qualified names
    if snippet_name in snippets:
        if snippets[snippet_name] is not None:
            snip_rec = snippets[snippet_name]
            snippets["{1}-{0}".format (snip_rec['primary'], snip_rec['qualifier'])] = snip_rec
            snippets[snippet_name] = None

        snippet_name = "{1}-{0}".format (primary_name, qualifier)

    # store the new snippet record
    snippets[snippet_name] = {'primary': primary_name, 'qualifier': qualifier, 'full_name': key, 'spec': rsrc_types[key]}

# remove empty snippet keys
for key in snippets.keys ():
    if snippets[key] is None:
        snippets.pop (key)

for key in snippets.keys ():
    snippet = snippets[key]
    ins_ctr = 1

    sfile = open ("{0}/{1}.cson".format (dest_prefix, key), 'w')

    sfile.write ("'.source.yaml':\n")
    sfile.write ("  '{0}':\n".format (key))
    sfile.write ("      'prefix': '{0}'\n".format (key))
    sfile.write ("      'body':\"\"\"\n")
    sfile.write ("          ${{{0}:{1}_name}}:\n".format (ins_ctr, key))
    sfile.write ("              Type: \"{0}\"\n".format (snippet['full_name']))
    sfile.write ("              Properties:\n")

    for pkey in sorted (snippet['spec']['Properties'].iterkeys ()):
        sprop = snippet['spec']['Properties'][pkey]

        ins_ctr += 1

        req_descriptor = 'optional'
        if sprop['Required']:
            req_descriptor = 'required'

        value_descriptor = 'value'
        if 'PrimitiveType' in sprop:
            value_descriptor = sprop['PrimitiveType']

        if 'Type' in sprop:
            if 'ItemType' in sprop:
                value_descriptor = sprop['ItemType']
            elif 'PrimitiveItemType' in sprop:
                value_descriptor = sprop['PrimitiveItemType']
            else:
                value_descriptor = sprop['Type']

            if sprop['Type'] == 'List':
                sfile.write ("                  {0}:                # {1}, list of {2}\n".format (pkey, req_descriptor, value_descriptor))
                sfile.write ("                      - ${{{0}:{1}}}\n".format (ins_ctr, value_descriptor))
            elif sprop['Type'] == 'Map':
                sfile.write ("                  {0}:                # {1}, map of {2}\n".format (pkey, req_descriptor, value_descriptor))
                sfile.write ("                      ${{{0}:{1}_key}}: ${{{2}:{1}_value}}\n".format (ins_ctr, value_descriptor, ins_ctr + 1))
                ins_ctr += 1
            else:
                sfile.write ("                  {0}: ${{{1}:{2}}}     # {3}\n".format (pkey, ins_ctr, value_descriptor, req_descriptor))
        else:
            sfile.write ("                  {0}: ${{{1}:{2}}}     # {3}\n".format (pkey, ins_ctr, value_descriptor, req_descriptor))

    sfile.write ("\"\"\"")

    sfile.close ()
