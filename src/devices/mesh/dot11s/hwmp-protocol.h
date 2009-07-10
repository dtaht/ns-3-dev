/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2008,2009 IITP RAS
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Authors: Kirill Andreev <andreev@iitp.ru>
 */


#ifndef HWMP_PROTOCOL_H
#define HWMP_PROTOCOL_H

#include "ns3/mesh-l2-routing-protocol.h"
#include "ns3/nstime.h"
#include "ns3/event-id.h"
#include "ie-dot11s-perr.h"
#include <vector>
#include <map>

namespace ns3 {
class MeshPointDevice;
class Packet;
class Mac48Address;
namespace dot11s {
class HwmpProtocolMac;
class HwmpRtable;
class IePreq;
class IePrep;
/**
 * \ingroup dot11s
 * 
 * \brief Hybrid wireless mesh protocol -- a routing protocol of IEEE 802.11s draft. 
 */
class HwmpProtocol : public MeshL2RoutingProtocol
{
public:
  static TypeId GetTypeId ();
  HwmpProtocol ();
  ~HwmpProtocol ();
  void DoDispose ();
  
  /// Route request, inherited from MeshL2RoutingProtocol
  bool RequestRoute (uint32_t  sourceIface, const Mac48Address source, const Mac48Address destination,
      Ptr<const Packet>  packet, uint16_t  protocolType, RouteReplyCallback  routeReply);
  /// Cleanup packet from all tags
  bool RemoveRoutingStuff (uint32_t fromIface, const Mac48Address source,
      const Mac48Address destination, Ptr<Packet>  packet, uint16_t&  protocolType);
  /** 
   * \brief Install HWMP on given mesh point. 
   * 
   * Installing protocol cause installing its interface MAC plugins.
   *  
   * Also MP aggregates all installed protocols, HWMP protocol can be accessed 
   * via MeshPointDevice::GetObject<dot11s::HwmpProtocol>();
   */
  bool Install (Ptr<MeshPointDevice>);
  void PeerLinkStatus(Mac48Address meshPontAddress, Mac48Address peerAddress, uint32_t interface,bool status);
  ///\brief This callback is used to obtain active neighbours on a
  //given interface
  ///\param interface is the interface ID
  void SetNeighboursCallback(Callback<std::vector<Mac48Address>, uint32_t> cb);
  ///\name Proactive PREQ mechanism:
  ///\{
  void SetRoot ();
  void UnsetRoot ();
  ///\}
  ///\brief Statistics:
  void Report (std::ostream &) const;
  void ResetStats ();
private:
  friend class HwmpProtocolMac;
  
  /// Like RequestRoute, but for unicast packets
  bool ForwardUnicast (uint32_t  sourceIface, const Mac48Address source, const Mac48Address destination,
      Ptr<Packet>  packet, uint16_t  protocolType, RouteReplyCallback  routeReply, uint32_t ttl);
  
  ///\name Interaction with HWMP MAC plugin
  //\{
  void ReceivePreq(IePreq preq, Mac48Address from, uint32_t interface, Mac48Address fromMp, uint32_t metric);
  void ReceivePrep(IePrep prep, Mac48Address from, uint32_t interface, Mac48Address fromMp, uint32_t metric);
  void ReceivePerr(std::vector<IePerr::FailedDestination>, Mac48Address from, uint32_t interface, Mac48Address fromMp);
  void SendPrep (
      Mac48Address src,
      Mac48Address dst,
      Mac48Address retransmitter,
      uint32_t initMetric,
      uint32_t originatorDsn,
      uint32_t destinationSN,
      uint32_t lifetime,
      uint32_t interface);
  /**
   * \brief Structure of path error: IePerr and list of receivers:
   * interfaces and MAC address
   */
  struct PathError
  {
    std::vector<IePerr::FailedDestination> destinations;
    /// interface-address
    std::vector<std::pair<uint32_t, Mac48Address> > receivers;
  };
  /**
   * \brief forms a path error information element when list of destination fails on a given interface
   * \attention removes all entries from routing table!
   */
  PathError MakePathError (std::vector<IePerr::FailedDestination> destinations);
  ///\brief Forwards a received path error
  void ForwardPathError (PathError perr);
  ///\brief Pasess a selg-generated PERR to interface-plugin
  void InitiatePathError (PathError perr);
  /// \return list of addresses where a PERR should be sent to
  std::vector<std::pair<uint32_t, Mac48Address> > GetPerrReceivers (std::vector<IePerr::FailedDestination> failedDest);
  
  /// \return list of addresses where a PERR should be sent to
  std::vector<Mac48Address> GetPreqReceivers (uint32_t interface);
  /// \return list of addresses where a broadcast should be
  //retransmitted
  std::vector<Mac48Address> GetBroadcastReceivers (uint32_t interface); 
  /**
   * \brief MAC-plugin asks wether the frame can be dropeed. Protocol automatically updates seqno.
   * 
   * \return true if frame can be dropped
   * \param uint32_t is the seqno
   * \param Mac48Address is the mesh source addrress of the frame
   */
  bool DropDataFrame(uint32_t, Mac48Address);
  //\}
private:
  /// Packet waiting its routing information
  struct QueuedPacket {
    Ptr<Packet> pkt; ///< the packet
    Mac48Address src; ///< src address
    Mac48Address dst; ///< dst address
    uint16_t protocol; ///< protocol number
    uint32_t inInterface; ///< incoming device interface ID. (if packet has come from upper layers, this is Mesh point ID)
    RouteReplyCallback reply; ///< how to reply
    
    QueuedPacket () : pkt(0), protocol(0), inInterface(0) {}
  };
  
  ///\name Methods related to Queue/Dequeue procedures
  //\{
  bool QueuePacket (QueuedPacket packet);
  QueuedPacket  DequeueFirstPacketByDst (Mac48Address dst);
  QueuedPacket  DequeueFirstPacket ();
  void ReactivePathResolved (Mac48Address dst);
  void ProactivePathResolved ();
  //\}
  ///\name Statistics:
  ///\{
  struct Statistics
  {
    uint16_t txUnicast;
    uint16_t txBroadcast;
    uint32_t txBytes;
    uint16_t droppedTtl;
    uint16_t totalQueued;
    uint16_t totalDropped;
    uint16_t initiatedPreq;
    uint16_t initiatedPrep;
    uint16_t initiatedPerr;

    void Print (std::ostream & os) const;
    Statistics () : txUnicast (0), txBroadcast (0), txBytes (0), droppedTtl (0), totalQueued (0), totalDropped (0), initiatedPreq (0), initiatedPrep (0), initiatedPerr (0) {}
  };
  Statistics m_stats;
  ///\}
  ///\name Methods responsible for path discovery retry procedure:
  //\{
  /** 
   * \brief checks when the last path discovery procedure was started for a given destination. 
   * 
   * If the retry counter has not achieved the maximum level - preq should not be sent
   */
  bool  ShouldSendPreq (Mac48Address dst);
  
  /** 
   * \brief Generates PREQ retry when retry timeout has expired and route is still unresolved. 
   * 
   * When PREQ retry has achieved the maximum level - retry mechanish should be cancelled
   */
  void  RetryPathDiscovery (Mac48Address dst, uint8_t numOfRetry);
  //\}
  
  ///\name Proactive Preq routines:
  //\{
  void SendProactivePreq ();
  //\}
  ///\return address of MeshPointDevice
  Mac48Address GetAddress (); 
private:
  typedef std::map<uint32_t, Ptr<HwmpProtocolMac> > HwmpProtocolMacMap;
  HwmpProtocolMacMap m_interfaces;
  Mac48Address m_address;
  uint32_t m_dataSeqno;
  uint32_t m_hwmpSeqno;
  uint32_t m_preqId;
  ///\name Sequence number filters
  //\{
  /// Data sequence number database
  std::map<Mac48Address, uint32_t> m_lastDataSeqno;
  /// DSN databse
  std::map<Mac48Address, uint32_t> m_lastHwmpSeqno;
  /// Metric database
  std::map<Mac48Address, uint32_t> m_lastHwmpMetric;
  //\}
  
  /// Routing table
  Ptr<HwmpRtable> m_rtable;
  
  ///\name Timers:
  //\{
  std::map<Mac48Address, EventId> m_preqTimeouts;
  EventId m_proactivePreqTimer;
  //Random start in Proactive PREQ propagation
  Time m_randomStart;
  //\}
  
  /// Packet Queue
  std::vector<QueuedPacket> m_rqueue; 
private:
  ///\name HWMP-protocol parameters (attributes of GetTypeId)
  //\{
  uint16_t m_maxQueueSize;
  uint8_t m_dot11MeshHWMPmaxPREQretries;
  Time m_dot11MeshHWMPnetDiameterTraversalTime;
  Time m_dot11MeshHWMPpreqMinInterval;
  Time m_dot11MeshHWMPperrMinInterval;
  Time m_dot11MeshHWMPactiveRootTimeout;
  Time m_dot11MeshHWMPactivePathTimeout;
  Time m_dot11MeshHWMPpathToRootInterval;
  Time m_dot11MeshHWMPrannInterval;
  bool m_isRoot;
  uint8_t m_maxTtl;
  uint8_t m_unicastPerrThreshold;
  uint8_t m_unicastPreqThreshold;
  uint8_t m_unicastDataThreshold;
  bool m_doFlag;
  bool m_rfFlag;
  //\}
  
  ///\name Methods needed by HwmpMacLugin to access protocol parameters:
  //\{
  bool GetDoFlag ();
  bool GetRfFlag ();
  Time GetPreqMinInterval ();
  Time GetPerrMinInterval ();
  uint8_t GetMaxTtl ();
  uint32_t GetNextPreqId ();
  uint32_t GetNextHwmpSeqno ();
  uint32_t GetActivePathLifetime ();
  uint8_t GetUnicastPerrThreshold ();
  //\}
  Callback <std::vector<Mac48Address>, uint32_t> m_neighboursCallback;
};
} //namespace dot11s
} //namespace ns3
#endif