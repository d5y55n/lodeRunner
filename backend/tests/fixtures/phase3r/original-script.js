
    // html 완전히 로드된 후 실행
    document.addEventListener('DOMContentLoaded', function()
    {
      //전역선언
      const showScore = document.getElementById('show_score');
      let realTimeModeId = null;

      //ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
      
      //1.차트 보기
      document.getElementById('symbol').addEventListener('change', function() 
      {
          const symbol = document.getElementById('symbol').value;
          const chartLink = `https://www.binance.com/en/futures/${symbol}`;
          document.getElementById('chartLook').href = chartLink;
          document.getElementById('chartLook').innerText = `차트 보기 (${symbol})`;
      });

      //ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
      
      //2.실시간 모드/60초 간격
      document.getElementById('real_time_entry').addEventListener('change', function()
      {

        const isChecked = document.getElementById('real_time_entry').checked;
        const symbol = document.getElementById('symbol');
        const entry = document.getElementById('entry');
        const selectPosition = document.getElementById('position');


        if(isChecked)
        {
          symbol.disabled = true;
          entry.disabled = true;
          selectPosition.disabled = true;
          showScore.disabled = true;


          async function realTimeMode()
          {
            const tickerUrl = `https://fapi.binance.com/fapi/v1/ticker/price?symbol=${symbol.value}`;
            try
            {
              const response = await axios.get(tickerUrl);
              const currentPrice = parseFloat(response.data.price);
              entry.value = currentPrice;

              showScore.click();
            }
            catch(e)
            {
              console.error("Error fetching ticker price:", e);
              alert("가격을 가져오는 데 실패했습니다. 나중에 다시 시도해주세요.");
            }
          }
          //최초 실행 1번
          realTimeMode();
          //60초마다 실행
          realTimeModeId = setInterval(realTimeMode, 60000);
        }
        else
        {
          symbol.disabled = false;
          entry.disabled = false;
          selectPosition.disabled = false;
          showScore.disabled = false;

          clearInterval(realTimeModeId);
        }
      });

      //ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
      
      //3.버튼 클릭시 스코어링
      showScore.addEventListener('click', async() => 
      {
          //필수 입력값 (코인 종류, 매수가, 포지션)
          const symbol = document.getElementById('symbol').value;
          const entry = parseFloat(document.getElementById('entry').value);
          const ls = document.getElementById('position').value;

          //로직 매개변수 : 인터벌당 데이터셋(필수)
          const dataSets =
          {
            '1d': { interval: '1d', totalCandles: 850 },
            '4h': { interval: '4h', totalCandles: 850*6 },
            '1h': { interval: '1h', totalCandles: 850*6*4 },
            '15m': { interval: '15m', totalCandles: 850*6*4*4 }
          }


          // 유효성 검사
          if (isNaN(entry)) 
          {
              alert("매수 가격을 입력해주세요.");
              return;
          }

          
          //for로 각 인터벌당 데이터 전부 가져오기
          async function getAllIntervalData(symbol, entry, ls, dataSets)
          {
            let scoreSum = 0;
            for(const[label, { interval, totalCandles}] of Object.entries(dataSets))
            {
              //하나의 인터벌 데이터 저장
              const candlesReceived = await getOneIntervalData(symbol, interval, totalCandles);

              //하나의 인터벌에 대한 로직 적용
              scoreSum += scoring(candlesReceived,interval,entry, ls);

              console.log(candlesReceived);
            }
            document.getElementById('web_scoreSum').innerText = scoreSum.toFixed(2);

          }
          
          //실행되는 부분
          fetchDbScore(entry);
          await getAllIntervalData(symbol, entry, ls, dataSets);

          
          //하나의 인터벌 데이터 가져오기
          async function getOneIntervalData(symbol, interval, totalCandles)
          {
            //바낸 API 번당 호출 최대 캔들 갯수 1500개
            let limit = 1500;

            if(totalCandles < limit)
            {
              limit = totalCandles; 
            }

            let endTime = Date.now();
            let candlesReceived = [];
            
            while(candlesReceived.length < totalCandles)
            {
              const url = `https://fapi.binance.com/fapi/v1/klines?symbol=${symbol}&interval=${interval}&limit=${limit}&endTime=${endTime}`;
              const response = await axios.get(url);
              const data =response.data;

              //받을 데이터 없으면 종료
              if(data.length === 0) break;

              //전 데이터랑 현 데이터랑 concat으로 배열 합치기
              candlesReceived = data.concat(candlesReceived);

              //다음 요청을 위해 제일 첫번째 캔들 시간 이전으로 이동
              const oldestOpenTime = data[0][0];
              endTime = oldestOpenTime - 1; 
             
            }

            return candlesReceived.slice(-totalCandles); // 최신 데이터만 반환
          }
          
          
          //하나의 인터벌에 대한 로직 적용
          function scoring(candlesReceived,interval,entry,ls)
          {
            let score=0;

            for(let i=0; i<candlesReceived.length-1; i++)
            {
              let before=candlesReceived[i];
              let after=candlesReceived[i+1];

              //Before캔들 세팅
              let Bdate = new Date(before[0]).toISOString().split('T')[0];
              let Bopen = parseFloat(before[1]);
              let Bhigh = parseFloat(before[2]);
              let Blow = parseFloat(before[3]);
              let Bclose = parseFloat(before[4]);
              
              //After캔들 세팅
              let Adate = new Date(after[0]).toISOString().split('T')[0];
              let Aopen = parseFloat(after[1]);
              let Ahigh = parseFloat(after[2]);
              let Alow = parseFloat(after[3]);
              let Aclose = parseFloat(after[4]);

              //인터벌 세팅
              //interval이 '1d'이면 0.022 '4h'이면 0.007 '1h'이면 0.004 '15m'이면 0.002
              let percent = 0;
              if(interval === '1d')
              {
                percent = 0.022;
              }
              else if(interval === '4h')
              {
                percent = 0.007;
              }
              else if(interval === '1h')
              {
                percent = 0.004;
              }
              else if(interval === '15m')
              {
                percent = 0.002;
              }

              

              //스코어링
              function adjustScore(base, adjustment) {
                if (ls === 'LONG') {
                  score += base * adjustment;
                } else if (ls === 'SHORT') {
                  score -= base * adjustment;
                }
              }

              function checkPriceRange(targetPrice) {
                if (entry < targetPrice * (1 + percent) && entry > targetPrice * (1 - percent)) {
                  return 1;
                } else if (
                  (entry >= targetPrice * (1 + percent) && entry < targetPrice * (1 + 1.5 * percent)) ||
                  (entry <= targetPrice * (1 - percent) && entry > targetPrice * (1 - 1.5 * percent))
                ) {
                  return 0.5;
                }
                return 0;
              }

              //전날 양봉, 다음날 음봉 (n구간)
              if (Bclose > Bopen && Aopen > Aclose) {
                const targetPrice = Bhigh > Ahigh ? Ahigh : Bhigh;
                const adjustment = checkPriceRange(targetPrice);
                if (adjustment > 0) {
                  adjustScore(-1, adjustment);
                }
              }
              
              //전날 음봉이고 그 다음날 양봉 (u지점)
              else if (Bclose < Bopen && Aopen < Aclose) {
                const targetPrice = Blow < Alow ? Alow : Blow;
                const adjustment = checkPriceRange(targetPrice);
                if (adjustment > 0) {
                  adjustScore(1, adjustment);
                }
              }                                                                           
                                            
            }

            //점수 테이블에 점수 넣기
            document.getElementById('web_' + interval).innerText = score;
            document.getElementById('web_entry').innerText = entry;
            document.getElementById('web_position').innerText = ls;
            return score;
          }


          //웹) DB 해당 엔트리 자동 조회
          async function fetchDbScore(entry)
          {
            //1. DB 테이블 싹다 집합
            const db_Entry = document.getElementById('db_entry');
            const db_Position = document.getElementById('db_position');
            const db_1d = document.getElementById('db_1d');
            const db_4h = document.getElementById('db_4h');
            const db_1h = document.getElementById('db_1h');
            const db_15m = document.getElementById('db_15m');
            const db_scoreSum = document.getElementById('db_scoreSum');
            const db_winrate_date = document.getElementById('db_winrate_date');


            //2. 지우개
            function clearDbTable()
            {
                db_entry.innerText = '';
                db_position.innerText = '';
                db_1d.innerText = '';
                db_4h.innerText = '';
                db_1h.innerText = '';
                db_15m.innerText = '';
                db_scoreSum.innerText = '';
                db_winrate_date.innerText = '';
            }
            //3. 지우개 호출
            clearDbTable();

            try
            {
                //4. 백엔드 API(
                const response = await axios.get('/api/db_score', { params: {entry}});
                const data = response.data; //응답 데이터 저장

                //5. 점수 합계 계산
                const scoreSum = data.score1d + data.score4h + data.score1h + data.score15m;

                //6. 테이블에 DB 데이터 넣기
                db_Entry.innerText = data.entry;
                db_Position.innerText = data.finalPosition;
                db_1d.innerText = data.score1d;
                db_4h.innerText = data.score4h;
                db_1h.innerText = data.score1h;
                db_15m.innerText = data.score15m;
                db_scoreSum.innerText = scoreSum.toFixed(2);
                db_winrate_date.innerText = `${data.winCount}승 ${data.loseCount}패 (${data.winningRate}%)
                - ${new Date(data.date).toISOString().split('T')[0]}`;
            }
            catch (error)
            {
              if (error.response && error.response.status === 404)
              {
                db_winrate_date.innerText = 'DB에 해당 데이터 없음';
              }
              else
              {
                console.error("DB 조회 중 오류 발생:", error);
                db_winrate_date.innerText = 'DB 조회 중 오류 발생';
              }
            }
          }


        });

        //ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ

      }); 
