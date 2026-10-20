const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
for(let i=0;i<60&&!document.getElementById('settings').classList.contains('active');i++)await wait(100);
const boot=await api('bootstrap');if(boot.configured||boot.demo)throw new Error('Fresh config test requires an unused QOL_CONFIG.');
if(!document.getElementById('settings').classList.contains('active'))throw new Error('Fresh installation did not show onboarding.');
if(document.getElementById('group-token').value!=='')throw new Error('Unexpected token in page.');
if(!document.getElementById('submit-day').disabled)throw new Error('Unconfigured saves should be disabled.');
const invite=await api('invitation',{format:'qol-group',version:1,group_name:'Fresh crew',timezone:'Asia/Tokyo',participants:[{name:'Alice',database_id:'a'.repeat(32)}]});
if(invite.participants.length!==1)throw new Error('Invitation validation failed.');
return {ok:true,fresh_config:'onboarding visible',token:'empty',unconfigured_save:'disabled',invitation_validation:'passed',mascot:document.body.dataset.mascot};
