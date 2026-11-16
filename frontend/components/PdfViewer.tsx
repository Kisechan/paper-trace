'use client';
import {useEffect,useMemo,useRef} from 'react';
import {PdfLoader,PdfHighlighter,Highlight,type IHighlight} from 'react-pdf-highlighter';
export type Citation={label:string;chunk_id:number;page_no:number;bbox:number[][];text:string;score:number};
export function toHighlight(c:Citation):IHighlight{
 const rects=c.bbox.map(([x1,y1,x2,y2])=>({x1,y1,x2,y2,width:1,height:1,pageNumber:c.page_no}));
 return {id:String(c.chunk_id),content:{text:c.text},comment:{text:'',emoji:''},position:{pageNumber:c.page_no,boundingRect:{x1:Math.min(...rects.map(r=>r.x1)),y1:Math.min(...rects.map(r=>r.y1)),x2:Math.max(...rects.map(r=>r.x2)),y2:Math.max(...rects.map(r=>r.y2)),width:1,height:1},rects}};
}
export default function PdfViewer({url,active}:{url:string;active?:Citation}){
 const scroll=useRef<(h:IHighlight)=>void>(()=>{});
 const highlights=useMemo(()=>active?.bbox.length?[toHighlight(active)]:[],[active]);
 useEffect(()=>{if(highlights[0])scroll.current(highlights[0])},[highlights]);
 return <div className="pdf-container"><PdfLoader url={url} workerSrc="/pdf.worker.min.mjs" beforeLoad={<div className="empty">正在读取原文…</div>} errorMessage={<div role="alert" className="empty">PDF 加载失败，请检查文件与服务。</div>}>{pdfDocument=><PdfHighlighter pdfDocument={pdfDocument} enableAreaSelection={()=>false} onScrollChange={()=>{}} scrollRef={fn=>{scroll.current=fn;if(highlights[0])fn(highlights[0])}} onSelectionFinished={()=>null} highlightTransform={(h,i,_setTip,_hideTip,_toScaled,_screenshot,isScrolledTo)=><Highlight key={i} position={h.position} comment={h.comment} isScrolledTo={isScrolledTo}/>} highlights={highlights}/>}</PdfLoader></div>
}
