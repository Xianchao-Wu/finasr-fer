from typing import Sequence, Tuple

def _edit_distance(ref: Sequence[str], hyp: Sequence[str]) -> Tuple[int,int,int,int]:
    n,m=len(ref),len(hyp)
    dp=[[(0,0,0,0) for _ in range(m+1)] for _ in range(n+1)]
    for i in range(1,n+1): dp[i][0]=(i,0,i,0)
    for j in range(1,m+1): dp[0][j]=(j,0,0,j)
    for i in range(1,n+1):
        for j in range(1,m+1):
            if ref[i-1]==hyp[j-1]:
                dp[i][j]=dp[i-1][j-1]
            else:
                a,b,c=dp[i-1][j-1],dp[i-1][j],dp[i][j-1]
                dp[i][j]=min([
                    (a[0]+1,a[1]+1,a[2],a[3]),
                    (b[0]+1,b[1],b[2]+1,b[3]),
                    (c[0]+1,c[1],c[2],c[3]+1)
                ], key=lambda x:x[0])
    return dp[n][m]

def word_error_rate(ref_text,hyp_text):
    r=ref_text.split(); h=hyp_text.split()
    cost,s,d,i=_edit_distance(r,h)
    return {"wer":cost/max(1,len(r)),"substitutions":s,"deletions":d,"insertions":i,"ref_words":len(r)}

def char_error_rate(ref_text,hyp_text):
    r=list(ref_text); h=list(hyp_text)
    cost,s,d,i=_edit_distance(r,h)
    return {"cer":cost/max(1,len(r)),"substitutions":s,"deletions":d,"insertions":i,"ref_chars":len(r)}
