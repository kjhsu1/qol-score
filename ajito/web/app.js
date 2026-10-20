'use strict';
const $=id=>document.getElementById(id);
// Older Big Sur WebKit has no native HTML dialog. Keep review accessible there too.
for(const dialog of document.querySelectorAll('dialog'))if(typeof dialog.showModal!=='function'){
 let veil=null,previous=null;
 Object.defineProperty(dialog,'open',{get:()=>dialog.hasAttribute('open')});
 dialog.showModal=()=>{previous=document.activeElement;veil=document.createElement('div');veil.className='fallback-backdrop';document.body.append(veil);dialog.classList.add('dialog-fallback');dialog.setAttribute('open','');dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.querySelector('button')?.focus();};
 dialog.close=()=>{dialog.removeAttribute('open');veil?.remove();veil=null;previous?.focus();};
 dialog.addEventListener('keydown',event=>{if(event.key==='Escape'){const cancel=new Event('cancel',{cancelable:true});dialog.dispatchEvent(cancel);if(!cancel.defaultPrevented)dialog.close();event.preventDefault();}if(event.key==='Tab'){const list=[...dialog.querySelectorAll('button:not(:disabled),input:not(:disabled)')];if(event.shiftKey&&document.activeElement===list[0]){list[list.length-1].focus();event.preventDefault();}else if(!event.shiftKey&&document.activeElement===list[list.length-1]){list[0].focus();event.preventDefault();}}});
}

function notifyOperation(){window.webkit?.messageHandlers?.operationState?.postMessage(Boolean(saving||setupBusy));}
let secret=location.hash.slice(1), state=null, preview=null, invitation=null, pendingEntry=null, previewSequence=0, setupBusy=false, saving=false;
history.replaceState(null,'',location.pathname);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const scoreText=value=>value==null?'—':Number(value).toLocaleString('en-US',{maximumFractionDigits:1});
function notice(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(notice.timer);notice.timer=setTimeout(()=>$('toast').hidden=true,5500);}
function banner(message){$('banner').textContent=message;$('banner').hidden=!message;}
async function api(path,data={}){
 const response=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-QOL-Token':secret},body:JSON.stringify(data)});
 const value=await response.json();if(!response.ok)throw new Error(value.error||'The request failed. Your form has been kept.');return value;
}
function streak(value){
 if(typeof value!=='number'||!Number.isFinite(value)||!Number.isInteger(value))return {text:'Unknown',kind:'neutral'};
 return value>0?{text:`Good · ${value}`,kind:'good'}:value<0?{text:`Bad · ${Math.abs(value)}`,kind:'bad'}:{text:'No streak',kind:'neutral'};
}
function entry(){
 const day=$('log-date').value;const stamp=id=>`${day}T${$(id).value.length===5?$(id).value+':00':$(id).value}`;
 const habits=Object.fromEntries([...document.querySelectorAll('[data-habit]')].map(b=>[b.dataset.habit,b.getAttribute('aria-pressed')==='true'?'Yes':'No']));
 return {todays_date:day,wake_time:stamp('wake'),sleep_time:stamp('bed'),...habits,social_media:$('social').value,time_focused:$('focused').value,diary:$('diary').value,offday_special_day:$('offday').checked?'Yes':'No'};
}
function showPage(name){
 if(setupBusy||saving){notice('Please let the current request finish.');return;}
 for(const el of document.querySelectorAll('.page'))el.classList.toggle('active',el.id===name);
 for(const el of document.querySelectorAll('[data-page]')){el.classList.toggle('active',el.dataset.page===name);el.setAttribute('aria-current',el.dataset.page===name?'page':'false');}
 $('page-label').textContent={daily:'DAILY CONSOLE',rankings:'CREW RANKINGS',history:'MISSION ARCHIVE',guide:'SCORING MANUAL',settings:'GROUP & SETTINGS',insights:'WEEKLY DEBRIEF',lab:'DAY LAB'}[name];
 window.scrollTo({top:0,behavior:document.body.classList.contains('motion-off')?'auto':'smooth'});
 if(name==='rankings')loadRankings();if(name==='history')loadHistory();if(name==='insights')loadInsights();if(name==='lab')loadLab();
}
function updateIdentity(data){
 state=data;$('profile-name').textContent=data.user||'Join your crew';$('profile-zone').textContent=data.timezone;$('avatar').textContent=(data.user||'?').slice(0,1).toUpperCase();
 $('welcome-copy').textContent=data.user?`${data.user}’s station. Ready when you are.`:"Your day, your score, your crew.";
 $('group-timezone').value=data.timezone;$('solo-timezone').value=data.timezone;
 $('breadcrumb').textContent=(data.group_name||'DORONBO HQ').toUpperCase();
 $('top-date').textContent=new Date(data.today+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}).toUpperCase();
 if(!$('log-date').value)$('log-date').value=data.today;
 if(data.demo)banner('DEMO CONSOLE — this preview uses sample crew data. Nothing is sent to Notion.');
 else if(data.config_error)banner('Your settings could not be read. Reconnect below; the original file will be backed up before replacement.');
 else banner('');
 $('submit-day').disabled=!data.configured;
 if(data.configured)loadLatest();
}
async function loadLatest(){
 try{const data=await api('latest');$('entry-number').textContent=String(data.number).padStart(3,'0');const s=streak(data.streak);$('your-streak').textContent=data.score==null?'Your first mission awaits':s.kind==='neutral'?s.text:`${s.kind==='good'?'Good':'Bad'} streak · ${Math.abs(data.streak)} entries`;$('latest-score').textContent=data.score==null?'Save your first day to start a streak.':`Latest: ${scoreText(data.score)} points · ${(data.date||'').slice(0,10)}`;}
 catch(error){$('entry-number').textContent='—';$('your-streak').textContent='Notion is unavailable';$('latest-score').textContent='Your form is ready. Check your connection and retry.';banner(error.message);}
}
async function updatePreview(){
 const seq=++previewSequence;preview=null;
 if(!$('focused').value||!$('social').value||!$('log-date').value||!$('wake').value||!$('bed').value){$('score').textContent='—';$('efficiency').textContent='—%';$('efficiency-fill').style.width='0%';$('gauge-fill').style.strokeDasharray='0 100';$('route').textContent='Awaiting your coordinates';$('score-caption').textContent='Fill in your minutes to power up the reactor.';return;}
 try{
 const result=await api('preview',entry());if(seq!==previewSequence)return;preview=result;
 $('score').textContent=scoreText(result.score);$('efficiency').textContent=result.efficiency+'%';$('efficiency-fill').style.width=Math.min(100,result.efficiency)+'%';$('awake-hours').textContent=`of ${(result.awake_minutes/60).toFixed(1)}h awake`;
 $('gauge-fill').style.strokeDasharray=`${result.score} 100`;$('gauge-fill').style.stroke=result.score>=65?'#bfd58b':'#df9b68';
 $('route').textContent=result.offday?'SPECIAL DAY · 100 POINTS':result.route==='healthy'?'HEALTHY ROUTE LEADING':'PRODUCTIVE ROUTE LEADING';
 $('score-caption').textContent=result.offday?'An agreed day off. Recharge your machinery.':result.score>=90?'90+ points. A strong day.':result.score>=65?'65+ points. This counts toward a good streak.':'Below 65. Check the deductions below.';
 $('breakdown').innerHTML=[['Healthy route deduction',result.healthy_deduction],['Productive route deduction',result.productive_deduction],['Wake timing',result.wake_deduction],['Bedtime timing',result.bed_deduction],['Social media',result.social_deduction]].map(([label,value])=>`<div><span>${label}</span><strong>−${scoreText(value)}</strong></div>`).join('')+(result.offday?'<div><span>Special-day override</span><strong>100</strong></div>':'');
 $('form-error').hidden=true;
 }catch(error){if(seq!==previewSequence)return;$('score').textContent='—';$('route').textContent='CHECK YOUR COORDINATES';$('score-caption').textContent=error.message;$('gauge-fill').style.strokeDasharray='0 100';$('efficiency').textContent='—%';$('efficiency-fill').style.width='0%';}
}
let previewTimer;function schedulePreview(){clearTimeout(previewTimer);previewTimer=setTimeout(updatePreview,180);}
async function loadRankings(){
 $('refresh-rankings').disabled=true;$('ranking-status').textContent='READING THE CREW…';
 $('ranking-rows').innerHTML='<tr><td colspan="5" class="table-status">Connecting to your crew’s Notion databases…</td></tr>';
 try{
 const result=await api('rankings'),rank=Object.entries(result.scores).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
 const names=new Set([...rank.map(r=>r[0]),...result.empty,...Object.keys(result.unavailable)]);
 $('ranking-status').textContent=Object.keys(result.unavailable).length?'PARTIAL RANKINGS':`${names.size} CREW MEMBERS`;
 $('podium').innerHTML=rank.slice(0,3).map(([name,score],index)=>{const s=streak(result.streaks[name]);return `<article class="podium-card ${index===0?'first':''}"><span class="podium-rank">${index===0?'★ CREW LEADER':'NO. '+String(index+1).padStart(2,'0')}</span><span class="avatar">${esc(name.slice(0,1).toUpperCase())}</span><h3>${esc(name)}</h3><div class="podium-score">${scoreText(score)}</div><span class="streak-chip ${s.kind}">${s.text}</span></article>`;}).join('');
 $('ranking-rows').innerHTML=rank.map(([name,score],index)=>{const s=streak(result.streaks[name]);return `<tr class="${name===state.user?'is-me':''}"><td>${String(index+1).padStart(2,'0')}</td><td><span class="avatar">${esc(name.slice(0,1).toUpperCase())}</span>${esc(name)}${name===state.user?' · You':''}</td><td class="score-cell">${scoreText(score)}</td><td>${esc(result.dates[name]||'—')}</td><td><span class="streak-chip ${s.kind}">${s.text}</span></td></tr>`;}).join('')+result.empty.map(name=>`<tr><td>—</td><td>${esc(name)}</td><td>No score</td><td>—</td><td>—</td></tr>`).join('')+Object.keys(result.unavailable).map(name=>`<tr><td>—</td><td>${esc(name)}</td><td>Unavailable</td><td>—</td><td>—</td></tr>`).join('');
 if(!names.size)$('ranking-rows').innerHTML='<tr><td colspan="5" class="table-status">No crew members yet. Import your invitation in Settings.</td></tr>';
 if(Object.keys(result.unavailable).length)notice('Some connections failed: '+Object.keys(result.unavailable).join(', ')+'. Available scores are shown.');
 }catch(error){$('podium').replaceChildren();$('ranking-status').textContent='CONNECTION FAILED';$('ranking-rows').innerHTML=`<tr><td colspan="5" class="table-status">${esc(error.message)}</td></tr>`;}
 finally{$('refresh-rankings').disabled=false;}
}
async function loadHistory(){
 $('refresh-history').disabled=true;$('history-chart').innerHTML='<p class="table-status">Opening the mission archive…</p>';
 try{
 const result=await api('history'),groups=new Map();
 for(const e of result.entries){if(typeof e.score!=='number'||!Number.isFinite(e.score)||e.score<0||e.score>100||!/^\d{4}-\d{2}-\d{2}/.test(e.date))continue;const day=e.date.slice(0,10);const list=groups.get(day)||[];list.push(e.score);groups.set(day,list);}
 const entries=[...groups.entries()].sort((a,b)=>a[0].localeCompare(b[0])).map(([date,scores])=>({date,score:scores.reduce((a,b)=>a+b,0)/scores.length}));
 const avg=entries.length?entries.reduce((s,e)=>s+e.score,0)/entries.length:null,best=entries.length?Math.max(...entries.map(e=>e.score)):null;
 $('history-stats').innerHTML=[['DAYS LOGGED',entries.length],['AVERAGE SCORE',scoreText(avg)],['PERSONAL BEST',scoreText(best)]].map(([label,value])=>`<div class="panel stat-card"><small>${label}</small><strong>${value}</strong></div>`).join('');
 if(!entries.length){$('history-chart').innerHTML='<p class="table-status">Your archive starts with your first saved day.</p>';return;}
 const width=900,height=280,left=35,right=25,top=20,bottom=35,x=i=>left+(entries.length===1?.5:i/(entries.length-1))*(width-left-right),y=s=>height-bottom-s/100*(height-top-bottom);
 const trend=entries.map((e,i)=>entries.slice(Math.max(0,i-6),i+1).reduce((s,e)=>s+e.score,0)/Math.min(7,i+1));
 const line=trend.map((s,i)=>`${i?'L':'M'}${x(i)},${y(s)}`).join(' '),points=entries.map((e,i)=>`<circle class="chart-dot" cx="${x(i)}" cy="${y(e.score)}" r="4"><title>${esc(e.date)}: ${scoreText(e.score)}</title></circle>`).join('');
 $('history-chart').innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Daily QOL scores and seven-entry average"><defs><linearGradient id="chart-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#b8d583" stop-opacity=".18"/><stop offset="100%" stop-color="#b8d583" stop-opacity="0"/></linearGradient></defs>${[0,25,50,75,100].map(s=>`<path class="chart-grid" d="M${left},${y(s)}H${width-right}"/><text class="chart-label" x="0" y="${y(s)+3}">${s}</text>`).join('')}<path class="chart-area" d="${line}L${x(entries.length-1)},${y(0)}L${x(0)},${y(0)}Z"/><path class="chart-line" d="${line}"/>${points}<text class="chart-label" x="${left}" y="${height-8}">${esc(entries[0].date)}</text><text class="chart-label" x="${width-right}" y="${height-8}" text-anchor="end">${esc(entries[entries.length-1].date)}</text></svg>`;
 }catch(error){$('history-chart').innerHTML=`<p class="table-status">${esc(error.message)}</p>`;}
 finally{$('refresh-history').disabled=false;}
}
for(const button of document.querySelectorAll('[data-page]'))button.addEventListener('click',()=>showPage(button.dataset.page));
document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();showPage('daily');});
for(const button of document.querySelectorAll('[data-habit]'))button.addEventListener('click',()=>{button.setAttribute('aria-pressed',button.getAttribute('aria-pressed')!=='true');schedulePreview();});
$('day-form').addEventListener('input',schedulePreview);
$('breakdown-toggle').addEventListener('click',()=>{const open=$('breakdown').hidden;$('breakdown').hidden=!open;$('breakdown-toggle').setAttribute('aria-expanded',open);});
$('refresh-rankings').addEventListener('click',loadRankings);$('refresh-history').addEventListener('click',loadHistory);
$('day-form').addEventListener('submit',async event=>{
 event.preventDefault();if(!state?.configured){showPage('settings');return;}
 try{const data=entry(),result=await api('preview',data);pendingEntry={...data,expected_user:state.user};$('review-description').textContent=`${state.user} · ${data.todays_date} · ${result.efficiency}% focus efficiency`;$('review-score').innerHTML=`${scoreText(result.score)}<small>/ 100</small>`;$('save-status').textContent='';$('review-dialog').showModal();}
 catch(error){$('form-error').textContent=error.message;$('form-error').hidden=false;}
});
$('confirm-submit').addEventListener('click',async()=>{
 if(saving||!pendingEntry)return;saving=true;notifyOperation();$('confirm-submit').disabled=true;
 for(const b of $('review-dialog').querySelectorAll('[data-close]'))b.disabled=true;
 $('save-status').textContent='Sending to Notion… Keep this window open.';
 try{const result=await api('submit',pendingEntry);$('review-dialog').close();$('success-message').textContent=`Entry ${result.entry_number} saved for ${state.user}: ${scoreText(result.qol_score)} points. ${streak(result.streak).text}.`;$('success-dialog').showModal();window.dispatchEvent(new CustomEvent('qol-saved'));pendingEntry=null;loadLatest();}
 catch(error){$('save-status').textContent=error.message;}
 finally{saving=false;notifyOperation();$('confirm-submit').disabled=false;for(const b of $('review-dialog').querySelectorAll('[data-close]'))b.disabled=false;}
});
$('review-dialog').addEventListener('cancel',event=>{if(saving)event.preventDefault();});
for(const button of document.querySelectorAll('[data-close]'))button.addEventListener('click',()=>$(button.dataset.close).close());
$('invitation-file').addEventListener('change',async()=>{
 const file=$('invitation-file').files[0];if(!file)return;
 try{if(file.size>128*1024)throw new Error('This file is too large to be an invitation.');invitation=await api('invitation',JSON.parse(await file.text()));$('invitation-summary').textContent=`${invitation.group_name} · ${invitation.participants.length} crew members`;$('group-name').innerHTML='<option value="">Choose your own name</option>'+invitation.participants.map(p=>`<option value="${esc(p.name)}">${esc(p.name)}</option>`).join('');if(state?.user&&invitation.participants.some(p=>p.name===state.user))$('group-name').value=state.user;}
 catch(error){invitation=null;$('invitation-summary').textContent=error.message;$('group-name').innerHTML='<option value="">Import a valid invitation</option>';}
});
async function connect(kind,form,payload,status){
 if(setupBusy)return;setupBusy=true;notifyOperation();const buttons=[...form.querySelectorAll('button,input,select')];buttons.forEach(b=>b.disabled=true);status.textContent='Checking every connection and required field…';
 try{const next=await api(kind,payload);$('day-form').reset();for(const b of document.querySelectorAll('[data-habit]'))b.setAttribute('aria-pressed','false');$('log-date').value=next.today;preview=null;schedulePreview();$('group-token').value='';$('solo-token').value='';updateIdentity(next);status.textContent='All connections passed. Welcome aboard.';setupBusy=false;showPage('daily');notice(`Connected as ${next.user}.`);}
 catch(error){status.textContent=error.message;}
 finally{setupBusy=false;notifyOperation();buttons.forEach(b=>b.disabled=false);}
}
$('group-form').addEventListener('submit',event=>{event.preventDefault();if(!invitation){$('setup-status').textContent='Import the organizer’s invitation first.';return;}connect('connect',$('group-form'),{invitation,name:$('group-name').value,token:$('group-token').value,timezone:$('group-timezone').value,accept:$('group-accept').checked},$('setup-status'));});
$('individual-form').addEventListener('submit',event=>{event.preventDefault();connect('individual',$('individual-form'),{name:$('solo-name').value,database:$('solo-db').value,token:$('solo-token').value,timezone:$('solo-timezone').value},$('solo-status'));});
$('export-invitation').addEventListener('click',async()=>{
 try{const data=await api('export',{name:state?.group_name||'QOL Friends'}),text=JSON.stringify(data,null,2)+'\n';
 if(window.webkit?.messageHandlers?.exportInvitation){window.webkit.messageHandlers.exportInvitation.postMessage(text);return;}
 const url=URL.createObjectURL(new Blob([text],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='QOL-Friends.qol-group.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
 }catch(error){notice(error.message);}
});

$('more-toggle').addEventListener('click',()=>{const open=$('more-menu').hidden;$('more-menu').hidden=!open;$('more-toggle').setAttribute('aria-expanded',open);});
async function loadInsights(){
 $('refresh-insights').disabled=true;$('insight-summary').textContent='Reading your saved scores…';
 try{const d=await api('insights');$('insight-stats').innerHTML=[['RECENT AVERAGE',scoreText(d.recent_average)],['GOOD DAYS',`${d.recent_good_days} / ${d.recent_count}`],['BEST STORED SCORE',scoreText(d.best_score)]].map(([label,value])=>`<div class="panel stat-card"><small>${label}</small><strong>${value}</strong></div>`).join('');
 const delta=d.previous_average==null||d.recent_average==null?null:Math.round((d.recent_average-d.previous_average)*10)/10;
 $('insight-summary').innerHTML=`<h2>${d.total_entries?`${d.total_entries} days in your archive.`:'Your debrief starts with your first day.'}</h2><p>${d.recent_count?`Your latest ${d.recent_count} logged days average ${scoreText(d.recent_average)}. ${d.recent_good_days} scored 65 or higher.`:'Log a day to begin.'}</p><p>${delta==null?'Log more days to compare two seven-entry windows.':`Compared with the preceding ${d.previous_count} entries: ${delta>0?'+':''}${scoreText(delta)} points on average.`}</p><p class="field-hint">${esc(d.scope)}</p>`;
 renderAnalysis(d);
 $('weekday-patterns').innerHTML=d.weekdays.map(row=>`<div class="pattern-row"><strong>${esc(row.day)}</strong><div class="pattern-bar"><i style="width:${row.average}%"></i></div><span>${scoreText(row.average)}</span><small>n=${row.count}</small></div>`).join('');
 }catch(error){$('insight-summary').textContent=error.message;}finally{$('refresh-insights').disabled=false;}
}
async function loadLab(){
 $('refresh-lab').disabled=true;
 try{const d=await api('day-lab',entry());$('lab-current').textContent=`Current projected score: ${scoreText(d.current)}`;$('lab-note').textContent=d.offday?'The special-day override is on, so changes still score 100.':'One change at a time. Nothing below edits your form or writes to Notion.';$('lab-scenarios').innerHTML=d.scenarios.map(s=>`<div class="scenario-row"><span>${esc(s.label)}</span><strong>${scoreText(s.score)}</strong><small class="${s.difference>0?'positive':''}">${s.difference>0?'+':''}${scoreText(s.difference)} points</small></div>`).join('');}
 catch(error){$('lab-current').textContent='Check the daily console first.';$('lab-note').textContent=error.message;$('lab-scenarios').replaceChildren();}finally{$('refresh-lab').disabled=false;}
}
function renderAnalysis(d){
 const points=d.focus_points||[],w=850,h=290,l=42,r=20,t=20,b=35,x=v=>l+v/100*(w-l-r),y=v=>h-b-v/100*(h-t-b);
 if(points.length){$('focus-scatter').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Focus efficiency versus stored QOL score">${[0,25,50,75,100].map(v=>`<path class="chart-grid" d="M${l},${y(v)}H${w-r}"/><text class="chart-label" x="0" y="${y(v)+3}">${v}</text><text class="chart-label" x="${x(v)}" y="${h-10}" text-anchor="middle">${v}%</text>`).join('')}${[60,70].map(v=>`<path d="M${x(v)},${t}V${h-b}" stroke="#74954b" stroke-dasharray="3 6"/>`).join('')}${points.map(p=>`<circle cx="${x(p.efficiency)}" cy="${y(p.score)}" r="${p.offday?6:4}" fill="${p.offday?'#dbaa62':'#b4cf85'}" fill-opacity=".7"><title>${esc(p.date)} · ${p.efficiency}% focus · ${scoreText(p.score)} score${p.offday?' · off day':''}</title></circle>`).join('')}</svg>`;}else $('focus-scatter').textContent='Not enough complete timing and focus inputs to plot yet.';
 $('focus-insight').textContent=`${points.length} days have complete inputs. ${d.correlation==null?'At least five non-off-day observations with varying values are needed for a descriptive correlation.':`Descriptive correlation: r = ${d.correlation}. Off days excluded.`}`;
 $('habit-analysis').innerHTML=(d.habits||[]).map(row=>`<div class="habit-analysis-row"><strong>${esc(row.label)}</strong><div><span>Yes · n=${row.yes_count}</span><div class="analysis-bar"><i style="width:${row.yes_average||0}%"></i></div><b>${scoreText(row.yes_average)}</b></div><div><span>No · n=${row.no_count}</span><div class="analysis-bar no"><i style="width:${row.no_average||0}%"></i></div><b>${scoreText(row.no_average)}</b></div><small>${row.yes_count>=5&&row.no_count>=5?`Observed difference: ${row.difference>0?'+':''}${scoreText(row.difference)} points.`:'Small sample: fewer than five days in one or both groups.'}</small></div>`).join('');
}
$('refresh-insights').addEventListener('click',loadInsights);$('refresh-lab').addEventListener('click',loadLab);
$('export-csv').addEventListener('click',async()=>{try{const d=await api('history');const yn=v=>v===true?'Yes':v===false?'No':'';const text='Date,QOL Score,Focus efficiency percent,Exercise,Outside,Conversation,Off day\r\n'+d.entries.filter(e=>/^\d{4}-\d{2}-\d{2}/.test(e.date)&&Number.isFinite(e.score)).map(e=>[e.date.slice(0,10),e.score,Number.isFinite(e.efficiency)?e.efficiency:'',yn(e.exercise),yn(e.outside),yn(e.talk),yn(e.offday)].join(',')).join('\r\n');if(window.webkit?.messageHandlers?.exportCSV){window.webkit.messageHandlers.exportCSV.postMessage(text);return;}const url=URL.createObjectURL(new Blob([text],{type:'text/csv'}));const a=document.createElement('a');a.href=url;a.download='QOL-scores.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}catch(error){notice(error.message);}});
let motionOff=matchMedia('(prefers-reduced-motion: reduce)').matches;function setMotion(){document.body.classList.toggle('motion-off',motionOff);$('motion-toggle').textContent=motionOff?'Motion off':'Motion on';$('motion-toggle').setAttribute('aria-pressed',motionOff);window.dispatchEvent(new CustomEvent('qol-motion',{detail:{paused:motionOff}}));}setMotion();$('motion-toggle').addEventListener('click',()=>{motionOff=!motionOff;setMotion();});
window.addEventListener('error',()=>notice('A display error occurred. Your entry has been kept; try reopening this page.'));
(async()=>{try{const data=await api('bootstrap');updateIdentity(data);if(!data.configured)showPage('settings');schedulePreview();}catch(error){banner('The local console could not connect: '+error.message);}})();
