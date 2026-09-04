import React,{useEffect,useState,useCallback} from 'react';
import {MessageCircle,MapPin,Menu,X,ArrowUpRight,ShieldCheck,ChevronDown,Upload,Lock,LogOut,LayoutDashboard,Users,Images,HelpCircle,Settings as SettingsIcon,Trash2,Plus,ExternalLink,Star,Phone,Instagram as InstagramIcon,Save,Edit3,Check,Clock} from 'lucide-react';
import './App.css';

const API=process.env.REACT_APP_BACKEND_URL;
if(!API){console.error('REACT_APP_BACKEND_URL não está definida. Configure-a no ambiente de build (Netlify → Site settings → Environment variables) e refaça o deploy.');}

const DEFAULT_WA='5531991310824';
const waLink=(phone,msg)=>`https://wa.me/${(phone||DEFAULT_WA).replace(/\D/g,'')}?text=${encodeURIComponent(msg)}`;

// Horário oficial Dinho Rodas: Seg-Sex 08h-18h · Sáb 08h-13h · Dom fechado
const SCHEDULE={0:[],1:[[8,18]],2:[[8,18]],3:[[8,18]],4:[[8,18]],5:[[8,18]],6:[[8,13]]};
function nowInSP(){
    const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/Sao_Paulo',weekday:'short',hour:'numeric',minute:'numeric',hour12:false}).formatToParts(new Date());
    const wd={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6}[parts.find(p=>p.type==='weekday').value];
    const h=parseInt(parts.find(p=>p.type==='hour').value,10)%24;
    const m=parseInt(parts.find(p=>p.type==='minute').value,10);
    return {day:wd,minutes:h*60+m};
}
function computeStatus(){
    const {day,minutes}=nowInSP();
    const ranges=SCHEDULE[day]||[];
    const open=ranges.some(([sh,eh])=>minutes>=sh*60&&minutes<eh*60);
    return {open,label:open?'Aberto agora':'Fechado agora'};
}

const demoData={services:[],testimonials:[],gallery:[],faqs:[],settings:{}};

function App(){const [route,setRoute]=useState(window.location.pathname); return route==='/admin'?<Admin onExit={()=>{window.history.pushState({},'','/');setRoute('/')}} />:<Public onAdmin={()=>{window.history.pushState({},'','/admin');setRoute('/admin')}}/>}

function useStatus(){
    const [status,setStatus]=useState(computeStatus());
    useEffect(()=>{const t=setInterval(()=>setStatus(computeStatus()),60000);return ()=>clearInterval(t);},[]);
    return status;
}

function Public({onAdmin}){
    const [data,setData]=useState(demoData),[menu,setMenu]=useState(false),[sent,setSent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[form,setForm]=useState({name:'',phone:'',vehicle:'',year:'',interest:'',message:''});
    const status=useStatus();
    const load=useCallback(()=>{if(!API)return;fetch(`${API}/api/public`).then(r=>r.json()).then(setData).catch(()=>{});},[]);
    useEffect(load,[load]);
    const s=data.settings||{};
    const phone=s.whatsapp||DEFAULT_WA;
    const mapsUrl=s.maps_url||'https://www.google.com/maps/search/?api=1&query=Rua+Jo%C3%A3o+Caetano+1013+Ambrosina+Belo+Horizonte';
    const openWA=(context)=>{
        if(API)fetch(`${API}/api/leads/click`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Visitante',phone:'',interest:context,source:`WhatsApp ${context}`})}).catch(()=>{});
        window.open(waLink(phone,`Olá! Vi o site da Dinho Rodas e gostaria de ${context.toLowerCase()}.`),'_blank');
    };
    const submit=async e=>{e.preventDefault();if(!API){setError('Site sem backend configurado.');return;}setBusy(true);setError('');const fd=new FormData();Object.entries(form).forEach(([k,v])=>fd.append(k,v));fd.append('origin','Formulário de orçamento');[...e.target.photos.files].forEach(f=>fd.append('photos',f));try{const r=await fetch(`${API}/api/quotes`,{method:'POST',body:fd});if(r.ok){setSent(true);setForm({name:'',phone:'',vehicle:'',year:'',interest:'',message:''})}else setError('Não foi possível enviar agora. Tente pelo WhatsApp.')}catch{setError('Sem conexão com o servidor. Tente pelo WhatsApp.')}finally{setBusy(false)}};
    return <div className="site">
        {!API&&<div className="config-warning" data-testid="api-config-warning">Configuração incompleta: defina REACT_APP_BACKEND_URL no Netlify e refaça o deploy.</div>}
        <div className="notice"><MapPin size={14}/> {s.address_short||'Ambrosina, Belo Horizonte'} <span>•</span><span className={`status-pill ${status.open?'open':'closed'}`} data-testid="status-pill"><Clock size={11}/>{status.label}</span><button onClick={onAdmin} data-testid="admin-access-button"><Lock size={12}/> Painel</button></div>
        <header><a className="brand" href="#top" data-testid="brand-link"><b>DR</b><span>DINHO <i>RODAS</i><small>LOJA • OFICINA • BH</small></span></a><button className="menu-btn" onClick={()=>setMenu(!menu)} data-testid="mobile-menu-button">{menu?<X/>:<Menu/>}</button><nav className={menu?'open':''}>{[['#services','Serviços'],['#quote','Orçamento'],['#gallery','Galeria'],...((data.testimonials&&data.testimonials.length>0)?[['#testimonials','Depoimentos']]:[]),['#faq','Dúvidas'],['#location','Localização']].map(([h,t])=><a href={h} onClick={()=>setMenu(false)} key={h} data-testid={`nav-${t.toLowerCase()}`}>{t}</a>)}<button className="wa-btn" onClick={()=>openWA('fazer um orçamento')} data-testid="header-whatsapp-button"><MessageCircle size={17}/> Falar no WhatsApp</button></nav></header>
        <main id="top">
            <section className="hero"><div className="hero-image"/><div className="hero-copy"><span className="eyebrow">RODAS • PNEUS • ATENDIMENTO ESPECIALIZADO</span><h1>Seu carro merece<br/><em>rodas à altura.</em></h1><p>Encontre as melhores opções para o seu carro e conte com atendimento especializado em Belo Horizonte.</p><div className="actions"><button className="primary" onClick={()=>openWA('fazer um orçamento')} data-testid="hero-whatsapp-button"><MessageCircle/> Falar no WhatsApp</button><a className="secondary" href="#quote" data-testid="hero-quote-button">Solicitar orçamento <ArrowUpRight size={18}/></a></div><div className="trust"><span><strong>4,8</strong><span className="stars">★★★★★</span><small>no Google</small></span><i/><span><strong>64</strong><small>avaliações</small></span><i/><span><ShieldCheck size={17}/><small>Presença local</small></span></div></div><div className="hero-tag">BH / MG <b>01</b></div></section>
            <section className="benefits"><div className="section-label">POR QUE A DINHO RODAS</div><h2>Confiança para escolher.<br/><span>Precisão para instalar.</span></h2><div className="benefit-grid">{[['01','Atendimento especializado','Orientação clara para você escolher com segurança.'],['02','Orçamento rápido','Envie os detalhes e fale com nossa equipe.'],['03','Atendimento presencial','Estamos em Ambrosina, Belo Horizonte.'],['04','Foco no seu carro','Soluções para diferentes estilos de veículos.']].map(x=><article key={x[0]} data-testid={`benefit-${x[0]}`}><b>{x[0]}</b><h3>{x[1]}</h3><p>{x[2]}</p></article>)}</div></section>
            <section id="services" className="dark-section"><div className="section-head"><div><div className="section-label">SOLUÇÕES</div><h2>Encontre o que<br/><span>seu carro precisa.</span></h2></div><a href="#quote" className="text-link" data-testid="services-quote-link">Quero saber mais <ArrowUpRight size={16}/></a></div><div className="service-grid">{data.services.map((x,i)=>{const src=x.image_url?(x.image_url.startsWith('/api/')?`${API}${x.image_url}`:x.image_url):null;return <article className="service-card" key={x.id} data-testid={`service-card-${x.id}`}>{src?<img src={src} alt={x.title} loading="lazy" style={{objectPosition:x.crop==='top'?'center top':x.crop==='bottom'?'center bottom':'center'}}/>:<div className="service-card-placeholder" aria-hidden="true"><SettingsIcon size={44}/></div>}<div><span>0{i+1} / {x.category||'Serviço'}</span><h3>{x.title}</h3><p>{x.description}</p><button onClick={()=>openWA(`saber mais sobre ${x.title}`)} data-testid={`service-whatsapp-${x.id}`}>Falar sobre isso <ArrowUpRight size={15}/></button></div></article>;})}</div></section>
            <section id="quote" className="quote-section"><div className="quote-intro"><div className="section-label">ATENDIMENTO DIRETO</div><h2>Faça seu<br/><span>orçamento.</span></h2><p>Conte o que você procura. Se puder, envie uma foto — ela ajuda nossa equipe a entender melhor o seu carro.</p><div className="quote-note"><MessageCircle/> <span>Ou fale direto<br/><b>pelo WhatsApp</b></span><button onClick={()=>openWA('fazer um orçamento')} data-testid="quote-whatsapp-button"><ArrowUpRight/></button></div></div><form onSubmit={submit} className="quote-form" data-testid="quote-form">{sent?<div className="success" data-testid="quote-success-message"><b>Recebemos seu pedido.</b><p>A equipe Dinho Rodas vai entrar em contato pelo WhatsApp.</p><button type="button" onClick={()=>setSent(false)} data-testid="new-quote-button">Enviar outro orçamento</button></div>:<><div className="form-row"><label>Seu nome<input required data-testid="quote-name-input" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="Como podemos chamar você?"/></label><label>WhatsApp<input required data-testid="quote-phone-input" value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} placeholder="(31) 99999-9999"/></label></div><div className="form-row"><label>Modelo do carro<input data-testid="quote-vehicle-input" value={form.vehicle} onChange={e=>setForm({...form,vehicle:e.target.value})} placeholder="Ex.: Honda Civic"/></label><label>Ano<input data-testid="quote-year-input" value={form.year} onChange={e=>setForm({...form,year:e.target.value})} placeholder="Ex.: 2022"/></label></div><label>O que você procura?<select data-testid="quote-interest-select" value={form.interest} onChange={e=>setForm({...form,interest:e.target.value})}><option value="">Selecione uma opção</option>{data.services.map(x=><option key={x.id}>{x.title}</option>)}<option>Outro assunto</option></select></label><label>Mensagem<textarea data-testid="quote-message-input" value={form.message} onChange={e=>setForm({...form,message:e.target.value})} placeholder="Conte um pouco mais sobre o que você precisa..."/></label><label className="file"><Upload size={18}/><span>Anexar fotos do carro ou roda <small>JPG, PNG • até 5 imagens</small></span><input name="photos" type="file" accept="image/*" multiple data-testid="quote-photo-input"/></label>{error&&<p className="error" data-testid="quote-error">{error}</p>}<button className="primary submit" disabled={busy} data-testid="quote-submit-button">{busy?'Enviando...':'Quero receber meu orçamento'} <ArrowUpRight size={18}/></button></>}</form></section>
            <section className="photo-cta"><div><div className="section-label">NÃO SABE QUAL ESCOLHER?</div><h2>Uma foto diz<br/><span>mais que mil dúvidas.</span></h2><p>Envie uma foto do seu carro e fale com nossa equipe.</p><button className="primary" onClick={()=>openWA('receber uma indicação para meu carro')} data-testid="photo-whatsapp-button"><MessageCircle/> Enviar foto pelo WhatsApp</button></div></section>
            <section id="gallery" className="gallery-section"><div className="section-head"><div><div className="section-label">NOSSO UNIVERSO</div><h2>Inspire-se<br/><span>na garagem.</span></h2></div></div>{data.gallery.length===0?<p className="empty-gallery">Galeria em atualização.</p>:<div className="gallery-grid">{data.gallery.map(x=>{const src=x.image_url?(x.image_url.startsWith('/api/')?`${API}${x.image_url}`:x.image_url):'';return <figure key={x.id} data-testid={`gallery-item-${x.id}`}><img src={src} alt={x.title||'imagem'} loading="lazy" style={{objectPosition:x.crop==='top'?'center top':x.crop==='bottom'?'center bottom':'center'}}/><figcaption><small>{x.category}</small><b>{x.title}</b></figcaption></figure>;})}</div>}</section>
            {data.testimonials&&data.testimonials.length>0&&<section id="testimonials" className="testimonials-section"><div className="section-head"><div><div className="section-label">QUEM JÁ VEIO, RECOMENDA</div><h2>O que dizem<br/><span>nossos clientes.</span></h2></div></div><div className="testimonials-grid">{data.testimonials.map(x=>{const rating=Math.max(0,Math.min(5,parseInt(x.rating,10)||5));return <article key={x.id} className="testimonial-card" data-testid={`testimonial-${x.id}`}><div className="testimonial-stars" aria-label={`${rating} de 5 estrelas`}>{Array.from({length:5}).map((_,i)=><Star key={i} size={15} fill={i<rating?'#f4a623':'none'} stroke={i<rating?'#f4a623':'#c9c9c9'}/>)}</div><p className="testimonial-content">"{x.content}"</p><footer className="testimonial-author"><b>{x.author||'Cliente Dinho Rodas'}</b>{x.role&&<small>{x.role}</small>}</footer></article>;})}</div></section>}
            <section id="faq" className="faq-section"><div><div className="section-label">DÚVIDAS</div><h2>Antes de<br/><span>vir, pergunte.</span></h2></div><div className="faq-list">{data.faqs.length===0?<p className="empty">Perguntas frequentes em breve.</p>:data.faqs.map(x=><details key={x.id} data-testid={`faq-item-${x.id}`}><summary>{x.question}<ChevronDown size={18}/></summary><p>{x.answer}</p></details>)}</div></section>
            <section id="location" className="location"><div><div className="section-label">ONDE ESTAMOS</div><h2>Visite a<br/><span>Dinho Rodas.</span></h2><p>{s.address||'Rua João Caetano, 1013 - Ambrosina, Belo Horizonte - MG, 30421-090'}</p><p className="hours">{s.hours||'Seg a Sex 08h às 18h · Sábado 08h às 13h'}<br/>{s.phone||'(31) 99131-0824'}</p><a className="secondary" href={mapsUrl} target="_blank" rel="noreferrer" data-testid="location-button">Como chegar <ExternalLink size={16}/></a></div><div className="map-placeholder"><MapPin size={30}/><b>Ambrosina / Belo Horizonte</b><small>{s.address_short||'Rua João Caetano, 1013'}</small></div></section>
        </main>
        <footer><span>DINHO <i>RODAS</i></span><small>© 2026 Dinho Rodas · {s.address_short||'Ambrosina, Belo Horizonte'}</small><button onClick={onAdmin} data-testid="footer-admin-button">Painel administrativo</button></footer>
        <button className="floating-wa" onClick={()=>openWA('falar com a equipe')} data-testid="floating-whatsapp-button"><MessageCircle/></button>
        <div className="mobile-bar"><button onClick={()=>openWA('falar com a equipe')} data-testid="mobile-whatsapp-button"><MessageCircle/> WhatsApp</button><a href="#quote" data-testid="mobile-quote-button">Orçamento</a><a href={mapsUrl} target="_blank" rel="noreferrer" data-testid="mobile-location-button">Como chegar</a></div>
    </div>;
}

function Admin({onExit}){
    const [token,setToken]=useState(localStorage.getItem('dinho_token'));
    const [login,setLogin]=useState({email:'',password:''});
    const [tab,setTab]=useState('dashboard'),[metrics,setMetrics]=useState({}),[items,setItems]=useState([]),[error,setError]=useState('');
    const tabs=[['dashboard','Visão geral',LayoutDashboard],['quotes','Orçamentos',MessageCircle],['leads','Leads',Users],['services','Serviços',SettingsIcon],['testimonials','Depoimentos',Star],['gallery','Galeria',Images],['faqs','FAQ',HelpCircle],['settings','Configurações',SettingsIcon]];
    const load=useCallback(()=>{
        if(!token||!API)return;
        fetch(`${API}/api/dashboard/metrics`,{headers:{Authorization:`Bearer ${token}`}}).then(r=>r.ok?r.json():{}).then(setMetrics).catch(()=>{});
        if(tab!=='dashboard'&&tab!=='settings')fetch(`${API}/api/admin/${tab}`,{headers:{Authorization:`Bearer ${token}`}}).then(r=>r.ok?r.json():[]).then(d=>setItems(Array.isArray(d)?d:[])).catch(()=>setItems([]));
    },[token,tab]);
    useEffect(load,[load]);
    const doLogin=async e=>{e.preventDefault();setError('');if(!API){setError('URL da API não configurada.');return;}try{const r=await fetch(`${API}/api/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(login)});const text=await r.text();let d;try{d=JSON.parse(text)}catch{setError('Resposta inválida do servidor. Verifique o backend.');return;}if(r.ok){localStorage.setItem('dinho_token',d.token);setToken(d.token)}else setError(d.detail||'Falha ao entrar')}catch{setError('Sem conexão com o backend.')}};
    if(!token)return <div className="admin-login"><div className="admin-box"><b className="admin-mark">DR</b><div className="section-label">ÁREA RESTRITA</div><h1>Painel<br/><span>Dinho Rodas.</span></h1>{error&&<p className="error" data-testid="login-error">{error}</p>}<form onSubmit={doLogin} data-testid="admin-login-form"><label>E-mail<input required type="email" data-testid="login-email" value={login.email} onChange={e=>setLogin({...login,email:e.target.value})}/></label><label>Senha<input required type="password" data-testid="login-password" value={login.password} onChange={e=>setLogin({...login,password:e.target.value})}/></label><button className="primary" data-testid="login-submit">Entrar no painel <ArrowUpRight size={17}/></button></form><button className="back" onClick={onExit} data-testid="back-to-site">← Voltar ao site</button></div></div>;
    return <div className="admin-shell"><aside><div className="admin-brand"><b>DR</b><span>DINHO RODAS<small>ADMIN</small></span></div>{tabs.map(([id,label,Icon])=><button className={tab===id?'active':''} onClick={()=>setTab(id)} key={id} data-testid={`admin-nav-${id}`}><Icon size={17}/>{label}</button>)}<button className="logout" onClick={()=>{localStorage.removeItem('dinho_token');setToken(null);onExit()}} data-testid="admin-logout"><LogOut size={16}/> Sair</button></aside><div className="admin-main"><header className="admin-top"><div><span className="section-label">OPERAÇÃO EM TEMPO REAL</span><h1>{tabs.find(x=>x[0]===tab)?.[1]}</h1></div><button onClick={onExit} data-testid="view-site-button">Ver site <ExternalLink size={15}/></button></header>{tab==='dashboard'?<Dashboard m={metrics}/>:tab==='settings'?<AdminSettings token={token}/>:tab==='services'?<AdminServices key="services" items={items} token={token} reload={load}/>:tab==='gallery'?<AdminGallery key="gallery" items={items} token={token} reload={load}/>:<AdminList key={tab} tab={tab} items={items} token={token} reload={load}/>}</div></div>;
}

function Dashboard({m}){return <div className="dash"><div className="metric-grid">{[['Leads recebidos',m.total_leads||0],['Orçamentos',m.total_quotes||0],['Novos pendentes',m.new_quotes||0],['Convertidos',m.converted||0]].map(x=><div className="metric" key={x[0]}><small>{x[0]}</small><b>{x[1]}</b><span>Atualizado agora</span></div>)}</div><div className="admin-panel"><div className="section-label">PRÓXIMOS PASSOS</div><h2>Seu conteúdo, no controle.</h2><p>Use o menu para acompanhar contatos, atualizar serviços, gerenciar galeria e manter as informações da Dinho Rodas sempre corretas.</p></div></div>}

// Field definitions per collection (avoid generic title/description fallback)
const FIELDS={
    faqs:[['question','Pergunta','text'],['answer','Resposta','textarea'],['order','Ordem','number']],
    services:[['title','Título','text'],['category','Categoria','text'],['description','Descrição','textarea'],['image_url','URL da imagem','text']],
    testimonials:[['author','Nome do cliente','text'],['content','Depoimento','textarea'],['rating','Nota (1 a 5)','number']],
    gallery:[['title','Título','text'],['category','Categoria','text'],['description','Descrição','text'],['image_url','URL da imagem','text']],
    quotes:[],leads:[],
};

function AdminList({tab,items,token,reload}){
    const [draft,setDraft]=useState({});
    const [editing,setEditing]=useState(null);
    const [saving,setSaving]=useState(false);
    const [message,setMessage]=useState('');
    const fields=FIELDS[tab]||[];
    const editable=fields.length>0;
    const create=async e=>{e.preventDefault();setSaving(true);setMessage('');try{const r=await fetch(`${API}/api/admin/${tab}`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({...draft,active:true})});if(r.ok){setDraft({});setMessage('Registro criado com sucesso.');reload()}else setMessage('Não foi possível criar. Verifique os campos.')}catch{setMessage('Sem conexão com o backend.')}finally{setSaving(false)}};
    const save=async(id,patch)=>{setSaving(true);try{const r=await fetch(`${API}/api/admin/${tab}/${id}`,{method:'PUT',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(patch)});if(r.ok){setMessage('Atualizado.');setEditing(null);reload()}else setMessage('Falha ao atualizar.')}catch{setMessage('Sem conexão.')}finally{setSaving(false)}};
    const remove=async id=>{if(!window.confirm('Excluir este registro?'))return;try{await fetch(`${API}/api/admin/${tab}/${id}`,{method:'DELETE',headers:{Authorization:`Bearer ${token}`}});reload()}catch{}};
    const label=tab==='quotes'?'orçamento':tab==='leads'?'lead':tab==='faqs'?'FAQ':tab==='testimonials'?'depoimento':tab==='gallery'?'foto':'serviço';
    return <div className="crud">
        {editable&&<form className="admin-panel add-form" onSubmit={create}>
            <div><div className="section-label">NOVO REGISTRO</div><h2>Adicionar {label}</h2></div>
            {fields.map(([key,ph,type])=>type==='textarea'?<textarea key={key} placeholder={ph} value={draft[key]||''} onChange={e=>setDraft({...draft,[key]:e.target.value})}/>:<input key={key} type={type} placeholder={ph} value={draft[key]||''} onChange={e=>setDraft({...draft,[key]:type==='number'?parseInt(e.target.value||'0',10):e.target.value})}/>)}
            <button className="primary" disabled={saving} data-testid={`add-${tab}-button`}><Plus size={16}/> {saving?'Salvando...':'Adicionar'}</button>
        </form>}
        {message&&<p className={message.includes('sucesso')||message==='Atualizado.'?'success-msg':'error'} data-testid="admin-message">{message}</p>}
        <div className="admin-panel records"><div className="records-head"><h2>Registros <span>{items.length}</span></h2>{tab==='quotes'&&<span className="demo-label">CRUD ATIVO</span>}</div>
            {items.length===0?<p className="empty">Nenhum registro encontrado ainda.</p>:items.map(x=>{
                const isQuoteLike=tab==='quotes'||tab==='leads';
                const editable2=FIELDS[tab]&&FIELDS[tab].length>0;
                return <div className="record" key={x.id} data-testid={`admin-record-${x.id}`}>
                    {isQuoteLike?<div className="record-quote"><b>{x.name||'Sem nome'}</b><small className="quote-detail"><Phone size={11}/> {x.phone||'—'} · {x.vehicle||'sem veículo'} {x.year?`(${x.year})`:''}</small>{x.interest&&<small><b>Interesse:</b> {x.interest}</small>}{x.message&&<small className="quote-msg">"{x.message}"</small>}{x.photos&&x.photos.length>0&&<div className="quote-photos">{x.photos.map((p,i)=><a key={i} href={`${API}${p}`} target="_blank" rel="noreferrer"><img src={`${API}${p}`} alt="anexo"/></a>)}</div>}<small className="quote-time">{new Date(x.created_at).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'})}</small></div>
                    :editing===x.id?<EditForm item={x} fields={FIELDS[tab]||[]} onSave={p=>save(x.id,p)} onCancel={()=>setEditing(null)}/>
                    :<div><b>{x.question||x.title||x.author||'Registro'}</b><small>{x.answer||x.description||x.content||''}</small></div>}
                    <div className="record-actions">
                        {isQuoteLike&&x.phone&&<a className="wa-quick" href={waLink(x.phone,`Olá ${x.name||''}, aqui é da Dinho Rodas!`)} target="_blank" rel="noreferrer" title="Falar no WhatsApp"><MessageCircle size={15}/></a>}
                        <span className={x.status==='Convertido'?'good':''}>{x.status||(x.active===false?'Inativo':'Ativo')}</span>
                        {editable2&&editing!==x.id&&<button onClick={()=>setEditing(x.id)} title="Editar" data-testid={`edit-${x.id}`}><Edit3 size={15}/></button>}
                        <button onClick={()=>remove(x.id)} title="Excluir" data-testid={`delete-${x.id}`}><Trash2 size={15}/></button>
                    </div>
                </div>;
            })}
        </div>
    </div>;
}

function EditForm({item,fields,onSave,onCancel}){
    const [patch,setPatch]=useState(()=>Object.fromEntries(fields.map(([k])=>[k,item[k]??''])));
    return <div className="edit-form">{fields.map(([key,ph,type])=>type==='textarea'?<textarea key={key} placeholder={ph} value={patch[key]||''} onChange={e=>setPatch({...patch,[key]:e.target.value})}/>:<input key={key} type={type} placeholder={ph} value={patch[key]||''} onChange={e=>setPatch({...patch,[key]:type==='number'?parseInt(e.target.value||'0',10):e.target.value})}/>)}<div className="edit-actions"><button className="primary" onClick={()=>onSave(patch)}><Save size={14}/> Salvar</button><button className="ghost" onClick={onCancel}>Cancelar</button></div></div>;
}

// ------- SERVIÇOS: CRUD dedicado (independente da Galeria) -------
const SERVICE_FIELDS=[['title','Título','text'],['category','Categoria (opcional)','text'],['description','Descrição','textarea'],['image_url','URL da imagem (opcional)','text']];

function AdminServices({items,token,reload}){
    const [draft,setDraft]=useState({title:'',category:'',description:'',image_url:''});
    const [file,setFile]=useState(null);
    const [preview,setPreview]=useState('');
    const [editing,setEditing]=useState(null);
    const [saving,setSaving]=useState(false);
    const [progress,setProgress]=useState('');
    const [message,setMessage]=useState('');
    const onPick=e=>{
        const f=e.target.files&&e.target.files[0];
        if(!f){setFile(null);setPreview('');return;}
        if(!/^image\/(png|jpe?g|webp)$/i.test(f.type)){setMessage('Formato não suportado. Use PNG, JPG ou WEBP.');return;}
        if(f.size>15*1024*1024){setMessage('Arquivo maior que 15MB.');return;}
        setMessage('');setFile(f);setPreview(URL.createObjectURL(f));
    };
    const uploadFile=async(f)=>{
        const fd=new FormData();fd.append('file',f);
        const r=await fetch(`${API}/api/admin/upload`,{method:'POST',headers:{Authorization:`Bearer ${token}`},body:fd});
        if(!r.ok){const t=await r.text();throw new Error(t||'Falha no upload');}
        return r.json();
    };
    const create=async e=>{
        e.preventDefault();
        if(!draft.title.trim()||!draft.description.trim()){setMessage('Informe título e descrição do serviço.');return;}
        setSaving(true);setMessage('');setProgress('');
        try{
            let image_url=(draft.image_url||'').trim();
            if(file){
                setProgress('Enviando imagem...');
                const up=await uploadFile(file);
                image_url=up.url;
            }
            setProgress('Salvando serviço...');
            const payload={title:draft.title.trim(),category:(draft.category||'').trim(),description:draft.description.trim(),image_url,active:true};
            const r=await fetch(`${API}/api/admin/services`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(payload)});
            if(r.ok){setDraft({title:'',category:'',description:'',image_url:''});setFile(null);setPreview('');setMessage('Serviço criado com sucesso.');reload();}
            else setMessage('Não foi possível criar o serviço.');
        }catch(err){setMessage(err.message||'Sem conexão com o backend.');}
        finally{setSaving(false);setProgress('');}
    };
    const save=async(id,patch)=>{setSaving(true);try{const r=await fetch(`${API}/api/admin/services/${id}`,{method:'PUT',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(patch)});if(r.ok){setMessage('Atualizado.');setEditing(null);reload();}else setMessage('Falha ao atualizar.');}catch{setMessage('Sem conexão.');}finally{setSaving(false);}};
    const remove=async id=>{if(!window.confirm('Excluir este serviço?'))return;try{await fetch(`${API}/api/admin/services/${id}`,{method:'DELETE',headers:{Authorization:`Bearer ${token}`}});reload();}catch{}};
    return <div className="crud">
        <form className="admin-panel add-form" onSubmit={create} data-testid="services-add-form">
            <div><div className="section-label">NOVO REGISTRO</div><h2>Adicionar serviço</h2></div>
            <input type="text" placeholder="Título" value={draft.title} onChange={e=>setDraft({...draft,title:e.target.value})} data-testid="service-title-input"/>
            <input type="text" placeholder="Categoria (opcional)" value={draft.category} onChange={e=>setDraft({...draft,category:e.target.value})} data-testid="service-category-input"/>
            <textarea placeholder="Descrição" value={draft.description} onChange={e=>setDraft({...draft,description:e.target.value})} data-testid="service-description-input"/>
            <label className="file" style={{display:'flex',alignItems:'center',gap:12,border:'1px dashed #bbb',padding:16,color:'#555',position:'relative',cursor:'pointer'}}>
                <Upload size={18}/>
                <span>{file?file.name:'Selecionar imagem do computador (opcional)'} <small style={{display:'block',color:'#999',fontWeight:400,textTransform:'none',letterSpacing:0,marginTop:4}}>PNG, JPG ou WEBP · até 15MB</small></span>
                <input type="file" accept="image/png,image/jpeg,image/webp" onChange={onPick} data-testid="service-file-input" style={{position:'absolute',inset:0,opacity:0,cursor:'pointer'}}/>
            </label>
            {preview&&<div data-testid="service-preview" style={{margin:'8px 0'}}><img src={preview} alt="prévia" style={{maxHeight:180,maxWidth:'100%',objectFit:'cover',border:'1px solid #ddd'}}/></div>}
            <details style={{fontSize:11,color:'#666'}}><summary style={{cursor:'pointer'}}>Ou usar URL externa</summary>
                <input type="text" placeholder="https://..." value={draft.image_url} onChange={e=>setDraft({...draft,image_url:e.target.value})} data-testid="service-image-input" style={{marginTop:8}}/>
            </details>
            {progress&&<p style={{fontSize:11,color:'#666'}} data-testid="service-progress">{progress}</p>}
            <button className="primary" disabled={saving} data-testid="add-services-button"><Plus size={16}/> {saving?'Salvando...':'Adicionar serviço'}</button>
        </form>
        {message&&<p className={message.includes('sucesso')||message==='Atualizado.'?'success-msg':'error'} data-testid="admin-message">{message}</p>}
        <div className="admin-panel records">
            <div className="records-head"><h2>Serviços cadastrados <span>{items.length}</span></h2></div>
            {items.length===0?<p className="empty">Nenhum serviço cadastrado ainda.</p>:items.map(x=><div className="record" key={x.id} data-testid={`admin-record-${x.id}`}>
                {editing===x.id?<EditForm item={x} fields={SERVICE_FIELDS} onSave={p=>save(x.id,p)} onCancel={()=>setEditing(null)}/>
                :<div style={{display:'flex',gap:12,alignItems:'center'}}>
                    {x.image_url&&<img src={x.image_url.startsWith('/api/')?`${API}${x.image_url}`:x.image_url} alt={x.title||'imagem'} style={{width:70,height:70,objectFit:'cover',border:'1px solid #eee'}}/>}
                    <div><b>{x.title||'Serviço'}</b><small>{x.description||''}</small>{x.category&&<small style={{color:'#999',display:'block',marginTop:4}}>Categoria: {x.category}</small>}</div>
                </div>}
                <div className="record-actions">
                    <span className={x.active===false?'':'good'}>{x.active===false?'Inativo':'Ativo'}</span>
                    {editing!==x.id&&<button onClick={()=>setEditing(x.id)} title="Editar" data-testid={`edit-${x.id}`}><Edit3 size={15}/></button>}
                    <button onClick={()=>remove(x.id)} title="Excluir" data-testid={`delete-${x.id}`}><Trash2 size={15}/></button>
                </div>
            </div>)}
        </div>
    </div>;
}

// ------- GALERIA: CRUD dedicado (independente de Serviços) com upload de arquivo -------
const GALLERY_FIELDS=[['title','Título','text'],['category','Categoria','text'],['description','Descrição','text'],['image_url','URL da imagem','text']];

function AdminGallery({items,token,reload}){
    const [file,setFile]=useState(null);
    const [preview,setPreview]=useState('');
    const [meta,setMeta]=useState({title:'',category:'',description:''});
    const [urlOnly,setUrlOnly]=useState('');
    const [editing,setEditing]=useState(null);
    const [saving,setSaving]=useState(false);
    const [progress,setProgress]=useState('');
    const [message,setMessage]=useState('');
    const onPick=e=>{
        const f=e.target.files&&e.target.files[0];
        if(!f){setFile(null);setPreview('');return;}
        if(!/^image\/(png|jpe?g|webp)$/i.test(f.type)){setMessage('Formato não suportado. Use PNG, JPG ou WEBP.');return;}
        if(f.size>15*1024*1024){setMessage('Arquivo maior que 15MB.');return;}
        setMessage('');setFile(f);setPreview(URL.createObjectURL(f));
    };
    const uploadFile=async(f)=>{
        const fd=new FormData();fd.append('file',f);
        const r=await fetch(`${API}/api/admin/upload`,{method:'POST',headers:{Authorization:`Bearer ${token}`},body:fd});
        if(!r.ok){const t=await r.text();throw new Error(t||'Falha no upload');}
        return r.json();
    };
    const create=async e=>{
        e.preventDefault();
        setSaving(true);setMessage('');setProgress('');
        try{
            let image_url=(urlOnly||'').trim();
            if(file){
                setProgress('Enviando imagem...');
                const up=await uploadFile(file);
                image_url=up.url;
            }
            if(!image_url){setMessage('Selecione um arquivo ou informe uma URL.');setSaving(false);setProgress('');return;}
            setProgress('Salvando na galeria...');
            const payload={title:(meta.title||'').trim(),category:(meta.category||'').trim(),description:(meta.description||'').trim(),image_url,active:true};
            const r=await fetch(`${API}/api/admin/gallery`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(payload)});
            if(r.ok){setFile(null);setPreview('');setMeta({title:'',category:'',description:''});setUrlOnly('');setMessage('Imagem adicionada com sucesso.');reload();}
            else setMessage('Não foi possível salvar na galeria.');
        }catch(err){setMessage(err.message||'Sem conexão com o backend.');}
        finally{setSaving(false);setProgress('');}
    };
    const save=async(id,patch)=>{setSaving(true);try{const r=await fetch(`${API}/api/admin/gallery/${id}`,{method:'PUT',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(patch)});if(r.ok){setMessage('Atualizado.');setEditing(null);reload();}else setMessage('Falha ao atualizar.');}catch{setMessage('Sem conexão.');}finally{setSaving(false);}};
    const remove=async id=>{if(!window.confirm('Excluir esta imagem?'))return;try{await fetch(`${API}/api/admin/gallery/${id}`,{method:'DELETE',headers:{Authorization:`Bearer ${token}`}});reload();}catch{}};
    return <div className="crud">
        <form className="admin-panel add-form" onSubmit={create} data-testid="gallery-add-form">
            <div><div className="section-label">NOVO REGISTRO</div><h2>Adicionar imagem</h2></div>
            <label className="file" style={{display:'flex',alignItems:'center',gap:12,border:'1px dashed #bbb',padding:16,color:'#555',position:'relative',cursor:'pointer'}}>
                <Upload size={18}/>
                <span>{file?file.name:'Selecionar arquivo do computador'} <small style={{display:'block',color:'#999',fontWeight:400,textTransform:'none',letterSpacing:0,marginTop:4}}>PNG, JPG ou WEBP · até 15MB</small></span>
                <input type="file" accept="image/png,image/jpeg,image/webp" onChange={onPick} data-testid="gallery-file-input" style={{position:'absolute',inset:0,opacity:0,cursor:'pointer'}}/>
            </label>
            {preview&&<div data-testid="gallery-preview" style={{margin:'8px 0'}}><img src={preview} alt="prévia" style={{maxHeight:180,maxWidth:'100%',objectFit:'cover',border:'1px solid #ddd'}}/></div>}
            <input type="text" placeholder="Título (opcional)" value={meta.title} onChange={e=>setMeta({...meta,title:e.target.value})} data-testid="gallery-title-input"/>
            <input type="text" placeholder="Categoria (opcional)" value={meta.category} onChange={e=>setMeta({...meta,category:e.target.value})} data-testid="gallery-category-input"/>
            <input type="text" placeholder="Descrição (opcional)" value={meta.description} onChange={e=>setMeta({...meta,description:e.target.value})} data-testid="gallery-description-input"/>
            <details style={{fontSize:11,color:'#666'}}><summary style={{cursor:'pointer'}}>Ou usar URL externa</summary>
                <input type="text" placeholder="https://..." value={urlOnly} onChange={e=>setUrlOnly(e.target.value)} data-testid="gallery-url-input" style={{marginTop:8}}/>
            </details>
            {progress&&<p style={{fontSize:11,color:'#666'}} data-testid="gallery-progress">{progress}</p>}
            <button className="primary" disabled={saving} data-testid="add-gallery-button"><Plus size={16}/> {saving?'Salvando...':'Adicionar imagem'}</button>
        </form>
        {message&&<p className={message.includes('sucesso')||message==='Atualizado.'?'success-msg':'error'} data-testid="admin-message">{message}</p>}
        <div className="admin-panel records">
            <div className="records-head"><h2>Imagens cadastradas <span>{items.length}</span></h2></div>
            {items.length===0?<p className="empty">Nenhuma imagem cadastrada ainda.</p>:items.map(x=><div className="record" key={x.id} data-testid={`admin-record-${x.id}`}>
                {editing===x.id?<EditForm item={x} fields={GALLERY_FIELDS} onSave={p=>save(x.id,p)} onCancel={()=>setEditing(null)}/>
                :<div style={{display:'flex',gap:12,alignItems:'center'}}>
                    {x.image_url&&<img src={x.image_url.startsWith('/api/')?`${API}${x.image_url}`:x.image_url} alt={x.title||'imagem'} style={{width:70,height:70,objectFit:'cover',border:'1px solid #eee'}}/>}
                    <div><b>{x.title||'Imagem'}</b><small>{x.description||''}</small>{x.category&&<small style={{color:'#999',display:'block',marginTop:4}}>{x.category}</small>}</div>
                </div>}
                <div className="record-actions">
                    <span className={x.active===false?'':'good'}>{x.active===false?'Inativo':'Ativo'}</span>
                    {editing!==x.id&&<button onClick={()=>setEditing(x.id)} title="Editar" data-testid={`edit-${x.id}`}><Edit3 size={15}/></button>}
                    <button onClick={()=>remove(x.id)} title="Excluir" data-testid={`delete-${x.id}`}><Trash2 size={15}/></button>
                </div>
            </div>)}
        </div>
    </div>;
}

const SETTINGS_FIELDS=[
    ['company_name','Nome da empresa','text','Identidade'],
    ['phone','Telefone (display)','text','Contato'],
    ['whatsapp','WhatsApp (somente números)','text','Contato'],
    ['whatsapp_display','WhatsApp exibido','text','Contato'],
    ['instagram','Instagram (URL)','text','Contato'],
    ['address','Endereço completo','textarea','Localização'],
    ['address_short','Endereço curto','text','Localização'],
    ['hours','Horário (texto exibido)','text','Localização'],
    ['maps_url','Google Maps (URL)','text','Localização'],
    ['meta_title','Título SEO','text','SEO'],
    ['meta_description','Descrição SEO','textarea','SEO'],
];

function AdminSettings({token}){
    const [settings,setSettings]=useState(null);
    const [saving,setSaving]=useState(false);
    const [message,setMessage]=useState('');
    const load=useCallback(()=>{fetch(`${API}/api/settings`).then(r=>r.json()).then(setSettings).catch(()=>setMessage('Falha ao carregar configurações.'));},[]);
    useEffect(load,[load]);
    if(!settings)return <div className="admin-panel"><p>Carregando configurações...</p></div>;
    const save=async e=>{e.preventDefault();setSaving(true);setMessage('');try{const r=await fetch(`${API}/api/settings`,{method:'PUT',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(settings)});if(r.ok){const d=await r.json();setSettings(d);setMessage('Configurações salvas com sucesso.')}else setMessage('Não foi possível salvar. Faça login novamente.')}catch{setMessage('Sem conexão com o backend.')}finally{setSaving(false)}};
    const groups=['Identidade','Contato','Localização','SEO'];
    return <form onSubmit={save} className="settings-form" data-testid="settings-form">
        <div className="admin-panel"><div><div className="section-label">CONFIGURAÇÕES GERAIS</div><h2>Informações da empresa</h2><p>Estas informações aparecem em todo o site público. Ao salvar, tudo é atualizado imediatamente.</p></div></div>
        {groups.map(g=><div key={g} className="admin-panel settings-group"><h3>{g}</h3>{SETTINGS_FIELDS.filter(([,,,gg])=>gg===g).map(([key,label,type])=><label key={key}>{label}{type==='textarea'?<textarea value={settings[key]||''} onChange={e=>setSettings({...settings,[key]:e.target.value})} data-testid={`setting-${key}`}/>:<input type={type} value={settings[key]||''} onChange={e=>setSettings({...settings,[key]:e.target.value})} data-testid={`setting-${key}`}/>}</label>)}</div>)}
        {message&&<p className={message.includes('sucesso')?'success-msg':'error'} data-testid="settings-message"><Check size={14}/> {message}</p>}
        <button className="primary" disabled={saving} data-testid="settings-save"><Save size={16}/> {saving?'Salvando...':'Salvar configurações'}</button>
    </form>;
}

export default App;
