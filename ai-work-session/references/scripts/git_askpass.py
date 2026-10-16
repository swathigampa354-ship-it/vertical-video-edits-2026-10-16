#!/usr/bin/env python3
"""Git askpass bridge. Reads an authorized token only from process environment.
Never put a token in this file, a remote URL, configuration, or a log.
"""
import os,sys
prompt=' '.join(sys.argv[1:]).lower()
if 'username'in prompt:
 print('x-access-token')
elif 'password'in prompt:
 token=os.environ.get('SESSION_ARCHIVE_GITHUB_TOKEN','')
 if not token:
  print('No authorized transient GitHub credential was supplied.',file=sys.stderr)
  raise SystemExit(1)
 print(token)
else:
 raise SystemExit(1)
