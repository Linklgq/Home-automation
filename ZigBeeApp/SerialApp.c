/*********************************************************************
 * INCLUDES
 */

#include <stdio.h>
#include <string.h>
#include "AF.h"
#include "OnBoard.h"
#include "OSAL_Tasks.h"
#include "SerialApp.h"
#include "ZDApp.h"
#include "ZDObject.h"
#include "ZDProfile.h"

#include "hal_drivers.h"
#include "hal_key.h"
#if defined ( LCD_SUPPORTED )
  #include "hal_lcd.h"
#endif
#include "hal_led.h"
#include "hal_uart.h"

#include <ioCC2530.h>
#define MYLED P2_0

/*********************************************************************
 * MACROS
 */

/*********************************************************************
 * CONSTANTS
 */

#if !defined( SERIAL_APP_PORT )
#define SERIAL_APP_PORT  0
#endif

#if !defined( SERIAL_APP_BAUD )
  //#define SERIAL_APP_BAUD  HAL_UART_BR_38400
  #define SERIAL_APP_BAUD  HAL_UART_BR_115200
#endif

// When the Rx buf space is less than this threshold, invoke the Rx callback.
#if !defined( SERIAL_APP_THRESH )
#define SERIAL_APP_THRESH  64
#endif

#if !defined( SERIAL_APP_RX_SZ )
#define SERIAL_APP_RX_SZ  128
#endif

#if !defined( SERIAL_APP_TX_SZ )
#define SERIAL_APP_TX_SZ  128
#endif

// Millisecs of idle time after a byte is received before invoking Rx callback.
#if !defined( SERIAL_APP_IDLE )
#define SERIAL_APP_IDLE  6
#endif

// Loopback Rx bytes to Tx for throughput testing.
#if !defined( SERIAL_APP_LOOPBACK )
#define SERIAL_APP_LOOPBACK  FALSE
#endif

// This is the max byte count per OTA message.
#if !defined( SERIAL_APP_TX_MAX )
#define SERIAL_APP_TX_MAX  80
#endif

#define SERIAL_APP_RSP_CNT  4

/*定义设备序号，用于与地址对应，每个终端不同，下载前修改*/
#define  DevNum  3//这个根据不同的终端在下载时进行改动<----------------------------------------------------------------------

// This list should be filled with Application specific Cluster IDs.
const cId_t SerialApp_ClusterList[SERIALAPP_MAX_CLUSTERS] =
{
  APP_CLUSTERID_CMD,
  APP_CLUSTERID_FEEDBACK,
  APP_CONNECTREQ_CLUSTER,            
  APP_CONNECTRSP_CLUSTER             
};

const SimpleDescriptionFormat_t SerialApp_SimpleDesc =
{
  SERIALAPP_ENDPOINT,              //  int   Endpoint;
  SERIALAPP_PROFID,                //  uint16 AppProfId[2];
  SERIALAPP_DEVICEID,              //  uint16 AppDeviceId[2];
  SERIALAPP_DEVICE_VERSION,        //  int   AppDevVer:4;
  SERIALAPP_FLAGS,                 //  int   AppFlags:4;
  SERIALAPP_MAX_CLUSTERS,          //  byte  AppNumInClusters;
  (cId_t *)SerialApp_ClusterList,  //  byte *pAppInClusterList;
  SERIALAPP_MAX_CLUSTERS,          //  byte  AppNumOutClusters;
  (cId_t *)SerialApp_ClusterList   //  byte *pAppOutClusterList;
};

endPointDesc_t SerialApp_epDesc =
{
  SERIALAPP_ENDPOINT,
 &SerialApp_TaskID,
  (SimpleDescriptionFormat_t *)&SerialApp_SimpleDesc,
  noLatencyReqs
};

/*********************************************************************
 * TYPEDEFS
 */

/*********************************************************************
 * GLOBAL VARIABLES
 */
devStates_t SampleApp_NwkState;   
uint8 SerialApp_TaskID;           // Task ID for internal task/event processing.

/*********************************************************************
 * EXTERNAL VARIABLES
 */

/*********************************************************************
 * EXTERNAL FUNCTIONS
 */

/*********************************************************************
 * LOCAL VARIABLES
 */

static uint8 SerialApp_MsgID;

static afAddrType_t SerialApp_TxAddr;
static uint8 SerialApp_TxSeq;
static uint8 SerialApp_TxBuf[SERIAL_APP_TX_MAX+1]; //用来保存协调器从串口收到的来自上位机树莓派的信息
static uint8 SerialApp_TxLen;

static afAddrType_t SerialApp_RxAddr;
static uint8 SerialApp_RxSeq;
static uint8 SerialApp_RspBuf[SERIAL_APP_RSP_CNT];

/*
用数组保存不同终端的地址，在树莓派记住编号与
电器名字的映射，编号就是这个数组的下标，编号
也是在终端发给协调者中的数据包中标识了
*/

#define AMSize 16
static uint16 AddrMap[AMSize] = {0};
static uint8 led3_state = 0;

//协调者发送失败的时候重试的次数
static int retry = 3;
static int curTryNum = 0;

/*********************************************************************
 * LOCAL FUNCTIONS
 */

static void SerialApp_ProcessMSGCmd( afIncomingMSGPacket_t *pkt );
static void SerialApp_Send(void);
static void SerialApp_Resp(void);
static void SerialApp_CallBack(uint8 port, uint8 event); 
static void SerialApp_DeviceConnect(void);              
static void SerialApp_DeviceConnectRsp(uint8*);         
static void SerialApp_ConnectReqProcess(uint8*);           

/*********************************************************************
 * @fn      SerialApp_Init
 *
 * @brief   This is called during OSAL tasks' initialization.
 *
 * @param   task_id - the Task ID assigned by OSAL.
 *
 * @return  none
 */
void SerialApp_Init( uint8 task_id )
{
  halUARTCfg_t uartConfig;

  SerialApp_TaskID = task_id;
  SerialApp_RxSeq = 0xC3;
  SampleApp_NwkState = DEV_INIT;       
  
  afRegister( (endPointDesc_t *)&SerialApp_epDesc );

  RegisterForKeys( task_id );
  //初始化串口
  uartConfig.configured           = TRUE;              // 2x30 don't care - see uart driver.
  uartConfig.baudRate             = SERIAL_APP_BAUD;//默认波特率
  uartConfig.flowControl          = FALSE;
  uartConfig.flowControlThreshold = SERIAL_APP_THRESH; // 2x30 don't care - see uart driver.
  uartConfig.rx.maxBufSize        = SERIAL_APP_RX_SZ;  // 2x30 don't care - see uart driver.
  uartConfig.tx.maxBufSize        = SERIAL_APP_TX_SZ;  // 2x30 don't care - see uart driver.
  uartConfig.idleTimeout          = SERIAL_APP_IDLE;   // 2x30 don't care - see uart driver.
  uartConfig.intEnable            = TRUE;              // 2x30 don't care - see uart driver.
  uartConfig.callBackFunc         = SerialApp_CallBack;

  //打开串口
  HalUARTOpen (SERIAL_APP_PORT, &uartConfig);

#if defined ( LCD_SUPPORTED )
  HalLcdWriteString( "SerialApp", HAL_LCD_LINE_2 );
#endif
  
  ZDO_RegisterForZDOMsg( SerialApp_TaskID, End_Device_Bind_rsp );
  ZDO_RegisterForZDOMsg( SerialApp_TaskID, Match_Desc_rsp );
  /*-----------------------------------传播方式--------------------------------------*/
  /*
  SampleApp_Periodic_DstAddr.addrMode = (afAddrMode_t)AddrBroadcast;//广播
  SampleApp_Periodic_DstAddr.endPoint = SAMPLEAPP_ENDPOINT;
  SampleApp_Periodic_DstAddr.addr.shortAddr = 0xFFFF;

  // Setup for the flash command's destination address - Group 1
  SampleApp_Flash_DstAddr.addrMode = (afAddrMode_t)afAddrGroup;//组播
  SampleApp_Flash_DstAddr.endPoint = SAMPLEAPP_ENDPOINT;
  SampleApp_Flash_DstAddr.addr.shortAddr = SAMPLEAPP_FLASH_GROUP;
  
  SampleApp_P2P_DstAddr.addrMode = (afAddrMode_t)Addr16Bit; //点播 
  SampleApp_P2P_DstAddr.endPoint = SERIALAPP_ENDPOINT; 
  SampleApp_P2P_DstAddr.addr.shortAddr = 0x0000;            //发给协调器
  */
}

/*********************************************************************
 * @fn      SerialApp_ProcessEvent
 *
 * @brief   Generic Application Task event processor.
 *
 * @param   task_id  - The OSAL assigned task ID.
 * @param   events   - Bit map of events to process.
 *
 * @return  Event flags of all unprocessed events.
 */
UINT16 SerialApp_ProcessEvent( uint8 task_id, UINT16 events )
{
  (void)task_id;  // Intentionally unreferenced parameter
  
  if ( events & SYS_EVENT_MSG )//收到ZigBee天线的信息
  {
    afIncomingMSGPacket_t *MSGpkt;

    while ( (MSGpkt = (afIncomingMSGPacket_t *)osal_msg_receive( SerialApp_TaskID )) )
    {
      switch ( MSGpkt->hdr.event )
      {
      case AF_INCOMING_MSG_CMD:
        SerialApp_ProcessMSGCmd( MSGpkt );
        break;
        
      case ZDO_STATE_CHANGE:
        SampleApp_NwkState = (devStates_t)(MSGpkt->hdr.status);
        if ( (SampleApp_NwkState == DEV_ZB_COORD)
            || (SampleApp_NwkState == DEV_ROUTER)
            || (SampleApp_NwkState == DEV_END_DEVICE) )
        {
            // Start sending the periodic message in a regular interval.
           // HalLedSet(HAL_LED_1, HAL_LED_MODE_ON);
            //终端联网成功后，发送自己的短地址
          if(SampleApp_NwkState != DEV_ZB_COORD){
              SerialApp_DeviceConnect();
              osal_start_timerEx(task_id, SERIALAPP_REPORT_ADDR, 100);   
          }else {
              //clear AddrMap
              memset(AddrMap, '\0', AMSize);
              osal_start_timerEx(task_id, SERIALAPP_CLEAR_ADDRMAP, 5000);
            }
        }
        else
        {
          // Device is no longer in the network
        }
        break;

      default:
        break;
      }

      osal_msg_deallocate( (uint8 *)MSGpkt );
    }

    return ( events ^ SYS_EVENT_MSG );
  }

  if ( events & SERIALAPP_SEND_EVT ) //表示从串口接收上位机信息并发送给特定对象的事件
  {
    //串口数据无线发送
    SerialApp_Send();
    return ( events ^ SERIALAPP_SEND_EVT );
  }

  if ( events & SERIALAPP_RESP_EVT )
  {
    //串口发送数据的响应
    //收到此数据后，表示可以无线发送下一个串口数据
    SerialApp_Resp();//
    return ( events ^ SERIALAPP_RESP_EVT );
  }
  
  //周期性的上报地址
  if (events & SERIALAPP_REPORT_ADDR){
      SerialApp_DeviceConnect();
      osal_start_timerEx(task_id, SERIALAPP_REPORT_ADDR, 1000);
  }
  
  if (events & SERIALAPP_CLEAR_ADDRMAP){
      memset(AddrMap, '\0', AMSize);
      osal_start_timerEx(task_id, SERIALAPP_CLEAR_ADDRMAP, 5000);     
  }

  return ( 0 );  // Discard unknown events.
}

/*********************************************************************
 * @fn      SerialApp_ProcessMSGCmd
 *
 * @brief   Data message processor callback. This function processes
 *          any incoming data - probably from other devices. Based
 *          on the cluster ID, perform the intended action.
 *
 * @param   pkt - pointer to the incoming message packet
 *
 * @return  TRUE if the 'pkt' parameter is being used and will be freed later,
 *          FALSE otherwise.
 */
void SerialApp_ProcessMSGCmd( afIncomingMSGPacket_t *pkt )
{
  uint8 stat;
  uint8 seqnb;
  uint8 delay;
  uint8 target;

  switch ( pkt->clusterId )
  {
  // A message with a serial data block to be transmitted on the serial port.
  case APP_CLUSTERID_CMD: //收到发送过来的数据通过串口输出到电脑显示
    // Store the address for sending and retrying.
    osal_memcpy(&SerialApp_RxAddr, &(pkt->srcAddr), sizeof( afAddrType_t ));

    //接收到的数据包的序列号
    seqnb = pkt->cmd.Data[0];
/*
    // Keep message if not a repeat packet
    //SerialApp_RxSeq用于记录上一次接收到的数据包的序列号
    //当前数据包的seqnb序列号总是比记录的序列号大1，或者是从0开始
    if ( (seqnb > SerialApp_RxSeq) ||                    // Normal
        ((seqnb < 0x80 ) && ( SerialApp_RxSeq > 0x80)) ) // Wrap-around
    {
        // Transmit the data on the serial port. 
        // 序列号正确，串口输出数据
        if ( HalUARTWrite( SERIAL_APP_PORT, pkt->cmd.Data+1, (pkt->cmd.DataLength-1) ) )
        {
          // Save for next incoming message
          SerialApp_RxSeq = seqnb;
          stat = OTA_SUCCESS;
        }
        else
        {
          stat = OTA_SER_BUSY;
        }
    }
    else
    {
        //序列号不正确
        stat = OTA_DUP_MSG;
    }
*/    
    stat = pkt->cmd.Data[2] - '0';
    target = pkt->cmd.Data[1] - '0';
    //关闭LED2
    if (pkt->cmd.Data[2] == '1'){
      stat = 1;
      HalLedSet(HAL_LED_2, HAL_LED_MODE_ON);
      //接负极，所以0为开，另一端接电源
      MYLED = 0;
    }
    else if (pkt->cmd.Data[2] == '0'){
      stat = 0;
      HalLedSet(HAL_LED_2, HAL_LED_MODE_OFF);
      MYLED = 1;
    }
    
    // Select approproiate OTA flow-control delay.
    //delay = (stat == OTA_SER_BUSY) ? SERIALAPP_NAK_DELAY : SERIALAPP_ACK_DELAY;

    // Build & send OTA response message.
    SerialApp_RspBuf[0] = target;
    SerialApp_RspBuf[1] = stat;
    //SerialApp_RspBuf[2] = LO_UINT16( delay );
    //SerialApp_RspBuf[3] = HI_UINT16( delay );
    osal_set_event( SerialApp_TaskID, SERIALAPP_RESP_EVT ); //收到数据后，发送一个响应事件
    osal_stop_timerEx(SerialApp_TaskID, SERIALAPP_RESP_EVT);
    break;

  // A response to a received serial data block.   
  // 发送数据包后接到响应消息
  case APP_CLUSTERID_FEEDBACK:
    char UartRespBuf[10];
    UartRespBuf[0] = pkt->cmd.Data[0] + '0';//终端序号,字符串形式
    UartRespBuf[1] = pkt->cmd.Data[1] + '0'; //终端状态，字符串形式
    HalUARTWrite(SERIAL_APP_PORT, UartRespBuf, 2);
    SerialApp_TxLen = 0;
    osal_start_timerEx( SerialApp_TaskID, SERIALAPP_SEND_EVT, 100);
    
    //osal_set_event(SerialApp_TaskID, SERIALAPP_SEND_EVT);
    break;

    //协调器接收到终端的连接消息
    case APP_CONNECTREQ_CLUSTER:
      SerialApp_ConnectReqProcess((uint8*)pkt->cmd.Data);

    //终端接收到协调器连接的消息  
    case APP_CONNECTRSP_CLUSTER:
      SerialApp_DeviceConnectRsp((uint8*)pkt->cmd.Data);
      
    default:
      break;
  }
}

/*********************************************************************
 * @fn      SerialApp_Send
 *
 * @brief   Send data OTA.
 *
 * @param   none
 *
 * @return  none
 */
static void SerialApp_Send(void)
{
#if SERIAL_APP_LOOPBACK
    if (SerialApp_TxLen < SERIAL_APP_TX_MAX)
    {
        SerialApp_TxLen += HalUARTRead(SERIAL_APP_PORT, SerialApp_TxBuf+SerialApp_TxLen+1,
                                                      SERIAL_APP_TX_MAX-SerialApp_TxLen);
    }
  
    if (SerialApp_TxLen)
    {
      (void)SerialApp_TxAddr;
      if (HalUARTWrite(SERIAL_APP_PORT, SerialApp_TxBuf+1, SerialApp_TxLen))
      {
        SerialApp_TxLen = 0;
      }
      else
      {
         //osal_set_event(SerialApp_TaskID, SERIALAPP_SEND_EVT); 
#if 0
          if (curTryNum < retry){
            curTryNum ++;
            osal_set_event(SerialApp_TaskID, SERIALAPP_SEND_EVT); 
          }
          else {
            curTryNum = 0;
          }
#endif
      }
    }
#else
// SerialApp_TxLen 不为 0 时 代表有数 据要发送或者正在发送 
// SerialApp_TxLen 为 0 时 代表没有数据发送或者已经发送 完了。发送端接收到接收端的确认信息后，
// 确定本次数据已经被接收到会将 SerialApp_TxLen 置 0 为接收下次数据作准备    
    if (!SerialApp_TxLen && 
        (SerialApp_TxLen = HalUARTRead(SERIAL_APP_PORT, SerialApp_TxBuf+1, SERIAL_APP_TX_MAX)))
    {
      // Pre-pend sequence number to the Tx message.
      SerialApp_TxBuf[0] = ++SerialApp_TxSeq;
    }
    
    uint8 target; //表示终端的编号
    uint16 endDevice_Addr;
    target = SerialApp_TxBuf[1] - '0'; //从串口收到的数据，串口数据第二个字节是终端序号，对应短地址，第三个字节是控制信息，目前，0表示关闭，1表示打开
    endDevice_Addr = AddrMap[target];
    //每个存储的地址只用一次，用完清零等待终端下一次上报地址
    AddrMap[target] = 0;
  /*有了这一段会导致运行失败，详细见20190406.txt*/
    if(endDevice_Addr == 0){/*如果为0说明这个序号没有对应终端*/
      SerialApp_TxBuf[1] = target + '0';
      SerialApp_TxBuf[2] = 'N';         
    }
      //点播传送
      SerialApp_TxAddr.addrMode = (afAddrMode_t)Addr16Bit;
      SerialApp_TxAddr.endPoint = SERIALAPP_ENDPOINT;
      SerialApp_TxAddr.addr.shortAddr = endDevice_Addr;
  
      HalLedSet(HAL_LED_2, HAL_LED_MODE_ON);
      if (SerialApp_TxLen)
      {
        if (afStatus_SUCCESS != AF_DataRequest(&SerialApp_TxAddr,
                                               (endPointDesc_t *)&SerialApp_epDesc,
                                                APP_CLUSTERID_CMD,
                                                SerialApp_TxLen+1, SerialApp_TxBuf,
                                                &SerialApp_MsgID, 0, AF_DEFAULT_RADIUS))
        {
          HalLedSet(HAL_LED_2, HAL_LED_MODE_OFF);
          osal_set_event(SerialApp_TaskID, SERIALAPP_SEND_EVT); 
#if 0       
          if (curTryNum < retry){
            curTryNum ++;
            osal_set_event(SerialApp_TaskID, SERIALAPP_SEND_EVT); 
          }
          else {
            curTryNum = 0;
          }
#endif         
          
        }
      }
    //}
#endif
}

/*********************************************************************
 * @fn      SerialApp_Resp
 *
 * @brief   Send data OTA.
 *
 * @param   none
 *
 * @return  none
 */
static void SerialApp_Resp(void)
{
  if (afStatus_SUCCESS != AF_DataRequest(&SerialApp_RxAddr,
                                         (endPointDesc_t *)&SerialApp_epDesc,
                                          APP_CLUSTERID_FEEDBACK,
                                          SERIAL_APP_RSP_CNT, SerialApp_RspBuf,
                                         &SerialApp_MsgID, 0, AF_DEFAULT_RADIUS))
  {
    osal_set_event(SerialApp_TaskID, SERIALAPP_RESP_EVT);
  }
}

/*********************************************************************
 * @fn      SerialApp_CallBack
 *
 * @brief   Send data OTA.
 *
 * @param   port - UART port.
 * @param   event - the UART port event flag.
 *
 * @return  none
 */
static void SerialApp_CallBack(uint8 port, uint8 event)
{
  (void)port;

  if ((event & (HAL_UART_RX_FULL | HAL_UART_RX_ABOUT_FULL | HAL_UART_RX_TIMEOUT)) &&
#if SERIAL_APP_LOOPBACK
      (SerialApp_TxLen < SERIAL_APP_TX_MAX))
#else
      !SerialApp_TxLen)
#endif
  {
    SerialApp_Send();
  }
}

/*********************************************************************
*********************************************************************/
void  SerialApp_DeviceConnect()              
{
#if ZDO_COORDINATOR
  
#else
  
  uint16 nwkAddr;
  uint16 parentNwkAddr;
  char buff[30] = {0};
  
//  HalLedBlink( HAL_LED_2, 3, 50, (1000 / 4) );
  
  nwkAddr = NLME_GetShortAddr();
  parentNwkAddr = NLME_GetCoordShortAddr();
  sprintf(buff, "parent:%d   self:%d\r\n", parentNwkAddr, nwkAddr);
  HalUARTWrite ( 0, (uint8*)buff, strlen(buff));
  
  SerialApp_TxAddr.addrMode = (afAddrMode_t)Addr16Bit;
  SerialApp_TxAddr.endPoint = SERIALAPP_ENDPOINT;
  SerialApp_TxAddr.addr.shortAddr = parentNwkAddr;
  
  buff[0] = HI_UINT16( nwkAddr );
  buff[1] = LO_UINT16( nwkAddr );
  buff[2] = DevNum;
  
  if ( AF_DataRequest( &SerialApp_TxAddr, &SerialApp_epDesc,
                       APP_CONNECTREQ_CLUSTER,
                       3,
                       (uint8*)buff,
                       &SerialApp_MsgID, 
                       0, 
                       AF_DEFAULT_RADIUS ) == afStatus_SUCCESS )
  {
  }
  else
  {
    // Error occurred in request to send.
  }
  
#endif    //ZDO_COORDINATOR
}

void SerialApp_DeviceConnectRsp(uint8 *buf)
{
#if ZDO_COORDINATOR
  
#else
  //SerialApp_TxAddr.addrMode = (afAddrMode_t)Addr16Bit;
  //SerialApp_TxAddr.endPoint = SERIALAPP_ENDPOINT;
  //SerialApp_TxAddr.addr.shortAddr = BUILD_UINT16(buf[1], buf[0]);
 
//if (buf[0] == 'O' && buf[1] == 'K')//终端接受到协调者的"OK"信息，点亮LED2  
    //HalLedSet(HAL_LED_2, HAL_LED_MODE_ON);
  //HalUARTWrite ( 0, "< connect success>\n", 23);
#endif
}

void SerialApp_ConnectReqProcess(uint8 *buf)
{
  uint16 nwkAddr;
  char buff[30] = {0};
  
  SerialApp_TxAddr.addrMode = (afAddrMode_t)Addr16Bit;
  SerialApp_TxAddr.endPoint = SERIALAPP_ENDPOINT;
  SerialApp_TxAddr.addr.shortAddr = BUILD_UINT16(buf[1], buf[0]);
  
  //在全局变量中保存终端的地址
  AddrMap[buf[2]] = SerialApp_TxAddr.addr.shortAddr;
  
  nwkAddr = NLME_GetShortAddr();
  
  //sprintf(buff, "self:%d   child:%d\r\n", nwkAddr, SerialApp_TxAddr.addr.shortAddr);
  //HalUARTWrite ( 0, (uint8*)buff, strlen(buff));
  
  //buff[0] = HI_UINT16( nwkAddr );
  //buff[1] = LO_UINT16( nwkAddr );
  //向终端回复"OK"，完成握手
  buff[0] = 'O';
  buff[1] = 'K';
  
  if ( AF_DataRequest( &SerialApp_TxAddr, &SerialApp_epDesc,
                       APP_CONNECTRSP_CLUSTER,
                       2,
                       (uint8*)buff,
                       &SerialApp_MsgID, 
                       0, 
                       AF_DEFAULT_RADIUS ) == afStatus_SUCCESS )
  {
  }
  else
  {
    // Error occurred in request to send.
  }
  
//  HalLedSet(HAL_LED_2, HAL_LED_MODE_ON);
  //HalUARTWrite ( 0, "< connect success>\n", 23);
}
