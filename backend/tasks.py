from celery import chain, shared_task
from .database import SessionLocal
from . import billing_engine, models
from .services.snmp_service import SNMPService
from .services.topology_service import TopologyDiscoveryService
from .services.fault_management_service import FaultManagementService
from .services.performance_analytics_service import PerformanceAnalyticsService
from datetime import datetime, timedelta
import asyncio
import logging

# Allow asyncio.run() to be used even when an event loop is already running.
import nest_asyncio
nest_asyncio.apply()

logger = logging.getLogger(__name__)

@shared_task
def run_daily_billing_jobs():
    """
    Enhanced Celery task to run all daily billing operations with comprehensive features.
    This task is scheduled by Celery Beat and includes:
    - Advanced invoice generation with multiple pricing models
    - Sophisticated dunning management with escalation
    - Comprehensive service reactivation reconciliation
    - Detailed billing analytics and reporting
    """
    # Each task runs in its own process, so it needs its own DB session.
    db = SessionLocal()
    try:
        print("==============================================")
        print("CELERY TASK: Starting Enhanced Daily Billing & Management Jobs")
        print("==============================================")
        
        # 1. Generate invoices with comprehensive billing engine
        print("\n--- Phase 1: Enhanced Invoice Generation ---")
        invoice_result = billing_engine.generate_invoices_for_due_customers(db)
        print(f"Invoice Generation Summary: {invoice_result}")
        
        print("\n---------------------------------------------\n")
        
        # 2. Process dunning management with escalation workflows
        print("--- Phase 2: Enhanced Dunning Management ---")
        dunning_result = billing_engine.suspend_services_for_overdue_customers(db)
        print(f"Dunning Management Summary: {dunning_result}")
        
        print("\n---------------------------------------------\n")

        # 3. Process service reactivation with comprehensive reconciliation
        print("--- Phase 3: Enhanced Service Reactivation ---")
        reactivation_result = billing_engine.reactivate_paid_customers_services(db)
        print(f"Service Reactivation Summary: {reactivation_result}")

        print("\n=============================================\n")
        print("CELERY TASK: Enhanced daily jobs completed successfully.")
        
        # Return comprehensive summary
        return {
            "status": "success",
            "invoice_generation": invoice_result,
            "dunning_management": dunning_result,
            "service_reactivation": reactivation_result,
            "message": "All enhanced billing jobs completed successfully."
        }

    except Exception as e:
        print(f"CELERY TASK ERROR: An unexpected error occurred during the enhanced job run: {e}")
        db.rollback()
        # Re-raise the exception so Celery can mark the task as FAILED
        raise
    finally:
        db.close()

@shared_task
def run_billing_analytics():
    """
    Generate comprehensive billing analytics and reports
    """
    db = SessionLocal()
    try:
        print("Starting billing analytics generation...")
        
        engine = billing_engine.get_billing_engine(db)
        
        # Generate various reports
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        
        revenue_report = engine.generate_financial_reports('revenue_summary', start_date, end_date)
        aging_report = engine.generate_financial_reports('aging_report', start_date, end_date)
        payment_report = engine.generate_financial_reports('payment_analysis', start_date, end_date)
        
        print(f"Analytics generated successfully")
        return {
            "status": "success",
            "revenue_report": revenue_report,
            "aging_report": aging_report,
            "payment_report": payment_report
        }
        
    except Exception as e:
        print(f"Error generating billing analytics: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@shared_task
def process_payment_allocation(payment_id: int, allocation_strategy: str = "oldest_first"):
    """
    Process automatic payment allocation for a specific payment
    """
    db = SessionLocal()
    try:
        print(f"Processing payment allocation for payment ID: {payment_id}")
        
        engine = billing_engine.get_billing_engine(db)
        from .billing_engine import PaymentAllocationStrategy
        
        strategy = PaymentAllocationStrategy(allocation_strategy)
        result = engine.process_payment_allocation(payment_id, strategy)
        
        db.commit()
        print(f"Payment allocation completed: {result}")
        return result
        
    except Exception as e:
        print(f"Error processing payment allocation: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# =============================================================================
# NETWORK MONITORING CELERY TASKS
# =============================================================================

@shared_task
def collect_snmp_data():
    """
    Collect SNMP monitoring data from all active profiles.
    Scheduled to run every 5 minutes.
    """
    async def _run():
        db = SessionLocal()
        try:
            logger.info("Starting SNMP data collection task")
            
            snmp_service = SNMPService(db)
            
            # Get all active SNMP profiles
            active_profiles = db.query(models.SNMPMonitoringProfile).filter(
                models.SNMPMonitoringProfile.is_active == True
            ).all()
            
            profile_ids = [profile.id for profile in active_profiles]
            
            if profile_ids:
                results = await snmp_service.bulk_collect_data(profile_ids)
                
                successful = sum(1 for success in results.values() if success)
                failed = len(results) - successful
                
                logger.info(f"SNMP data collection completed: {successful} successful, {failed} failed")
                
                return {
                    "status": "success",
                    "profiles_processed": len(profile_ids),
                    "successful_collections": successful,
                    "failed_collections": failed,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                logger.info("No active SNMP profiles found")
                return {
                    "status": "success",
                    "message": "No active SNMP profiles to process",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in SNMP data collection task: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    return asyncio.run(_run())

@shared_task
def collect_performance_data():
    """
    Collect performance analytics data from all monitored devices.
    Scheduled to run every 5 minutes.
    """
    async def _run():
        db = SessionLocal()
        try:
            logger.info("Starting performance data collection task")
            
            analytics_service = PerformanceAnalyticsService(db)
            result = await analytics_service.collect_performance_data()
            
            logger.info(f"Performance data collection completed: {result}")
            
            return {
                "status": "success",
                "collection_result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in performance data collection task: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    return asyncio.run(_run())

@shared_task
def detect_network_incidents():
    """
    Run automated network incident detection.
    Scheduled to run every 10 minutes.
    """
    async def _run():
        db = SessionLocal()
        try:
            logger.info("Starting network incident detection task")
            
            fault_service = FaultManagementService(db)
            incidents = await fault_service.detect_incidents()
            
            logger.info(f"Incident detection completed: {len(incidents)} new incidents created")
            
            return {
                "status": "success",
                "incidents_created": len(incidents),
                "incident_numbers": [inc.incident_number for inc in incidents],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in incident detection task: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    return asyncio.run(_run())

@shared_task
def escalate_incidents():
    """
    Run automated incident escalation.
    Scheduled to run every 30 minutes.
    """
    async def _run():
        db = SessionLocal()
        try:
            logger.info("Starting incident escalation task")
            
            fault_service = FaultManagementService(db)
            escalated = await fault_service.escalate_incidents()
            
            logger.info(f"Incident escalation completed: {len(escalated)} incidents escalated")
            
            return {
                "status": "success",
                "incidents_escalated": len(escalated),
                "escalated_numbers": [inc.incident_number for inc in escalated],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in incident escalation task: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    return asyncio.run(_run())

@shared_task
def auto_resolve_incidents():
    """
    Run automated incident resolution.
    Scheduled to run every 15 minutes.
    """
    async def _run():
        db = SessionLocal()
        try:
            logger.info("Starting automated incident resolution task")
            
            fault_service = FaultManagementService(db)
            resolved = await fault_service.auto_resolve_incidents()
            
            logger.info(f"Auto-resolution completed: {len(resolved)} incidents resolved")
            
            return {
                "status": "success",
                "incidents_resolved": len(resolved),
                "resolved_numbers": [inc.incident_number for inc in resolved],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in auto-resolution task: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    return asyncio.run(_run())

@shared_task
def refresh_topology_status():
    """
    Refresh network topology device status.
    Scheduled to run every 10 minutes.
    """
    async def _run():
        db = SessionLocal()
        try:
            logger.info("Starting topology status refresh task")
            
            topology_service = TopologyDiscoveryService(db)
            await topology_service.refresh_device_status()
            
            logger.info("Topology status refresh completed")
            
            return {
                "status": "success",
                "message": "Device status refresh completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in topology status refresh task: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    return asyncio.run(_run())

@shared_task
def generate_network_analytics():
    """
    Generate comprehensive network analytics and reports.
    Scheduled to run daily.
    """
    async def _run():
        db = SessionLocal()
        try:
            logger.info("Starting network analytics generation task")
            
            analytics_service = PerformanceAnalyticsService(db)
            fault_service = FaultManagementService(db)
            
            # Generate performance reports for the last 24 hours
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=1)
            
            performance_report = await analytics_service.generate_performance_report(
                start_date=start_date,
                end_date=end_date
            )
            
            # Generate incident statistics
            incident_stats = await fault_service.get_incident_statistics(days=1)
            
            logger.info("Network analytics generation completed")
            
            return {
                "status": "success",
                "performance_report": {
                    "total_data_points": performance_report.get('total_data_points', 0),
                    "metrics_analyzed": len(performance_report.get('metrics_analyzed', [])),
                    "devices_analyzed": len(performance_report.get('devices_analyzed', []))
                },
                "incident_statistics": {
                    "total_incidents": incident_stats.get('total_incidents', 0),
                    "auto_resolved_count": incident_stats.get('auto_resolved_count', 0),
                    "escalated_count": incident_stats.get('escalated_count', 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in network analytics generation task: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    return asyncio.run(_run())

@shared_task
def cleanup_old_monitoring_data(retention_days: int = 90):
    """
    Clean up old monitoring data to maintain database performance.
    Scheduled to run weekly.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting monitoring data cleanup (retention: {retention_days} days)")
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        snmp_deleted = db.query(models.SNMPMonitoringData).filter(
            models.SNMPMonitoringData.timestamp < cutoff_date
        ).delete()
        
        performance_deleted = db.query(models.PerformanceData).filter(
            models.PerformanceData.timestamp < cutoff_date
        ).delete()
        
        bandwidth_deleted = db.query(models.BandwidthUsageLog).filter(
            models.BandwidthUsageLog.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        total_deleted = snmp_deleted + performance_deleted + bandwidth_deleted
        
        logger.info(f"Cleanup completed: {total_deleted} records deleted")
        
        return {
            "status": "success",
            "records_deleted": {
                "snmp_data": snmp_deleted,
                "performance_data": performance_deleted,
                "bandwidth_data": bandwidth_deleted,
                "total": total_deleted
            },
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in monitoring data cleanup task: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@shared_task
def run_network_discovery(start_ip: str, subnet_mask: str = "/24", community: str = "public"):
    """
    Run network topology discovery for a specified subnet.
    Can be triggered manually or scheduled.
    """
    async def _run():
        db = SessionLocal()
        try:
            logger.info(f"Starting network discovery for {start_ip}{subnet_mask}")
            
            topology_service = TopologyDiscoveryService(db)
            result = await topology_service.discover_network_topology(
                start_ip=start_ip,
                subnet_mask=subnet_mask,
                community=community
            )
            
            logger.info(f"Network discovery completed: {result['devices_discovered']} devices, {result['connections_discovered']} connections")
            
            return {
                "status": "success",
                "discovery_result": {
                    "devices_discovered": result['devices_discovered'],
                    "connections_discovered": result['connections_discovered'],
                    "subnet": result['subnet']
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in network discovery task: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    return asyncio.run(_run())


@shared_task
def log_monitoring_completion(previous_task_result):
    """Logs the successful completion of the monitoring workflow chain."""
    logger.info("Comprehensive network monitoring workflow completed successfully.")
    logger.debug(f"Final result from chain: {previous_task_result}")
    return {"status": "success", "message": "Workflow finished."}


@shared_task
def run_comprehensive_network_monitoring():
    """
    Run comprehensive network monitoring workflow using a Celery chain.
    This is a master task that coordinates multiple monitoring activities by queueing them.
    Scheduled to run every hour.
    """
    logger.info("Queueing comprehensive network monitoring workflow.")

    # This chain ensures tasks run sequentially in a non-blocking way.
    # If any task fails, the chain stops by default.
    # The '.s()' creates a 'signature' of the task, a building block for workflows.
    workflow = chain(
        collect_snmp_data.s(),
        collect_performance_data.s(),
        detect_network_incidents.s(),
        auto_resolve_incidents.s(),
        refresh_topology_status.s(),
        log_monitoring_completion.s()  # A final task to log success.
    )
    workflow.apply_async()

    logger.info("Comprehensive network monitoring workflow has been queued.")
    return {"status": "queued", "message": "Network monitoring workflow started."}