const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
for(let i=0;i<100&&!document.getElementById('profile-name').textContent;i++)await wait(100);
const boot=await api('bootstrap');if(!boot.configured||boot.demo)throw new Error('This test requires the existing real account.');
const latest=await api('latest');const ranks=await api('rankings');const entries=await api('history');const insights=await api('insights');
if(Object.keys(ranks.unavailable).length)throw new Error('Some crew connections are unavailable.');
if(Object.keys(ranks.scores).length+ranks.empty.length!==boot.participants.length)throw new Error('Incomplete roster.');
return {ok:true,mode:'read-only; no write endpoints called',participants:boot.participants,latest_entry_read:latest.number>0,history_entries_read:entries.entries.length,analysis_days:insights.total_entries,mascot:document.body.dataset.mascot};
